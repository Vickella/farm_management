import frappe
from frappe.utils import flt, today
from farm_management.server_validation import get_farm_context, validate_date_order, validate_farm_type_assignment


def validate_agriculture_project(doc, method=None):
    ptype = doc.get("agriculture_project_type")
    if not ptype:
        return
    project_type = get_agriculture_project_type(ptype)
    if project_type:
        doc.agriculture_farm_type = project_type.farm_type
    else:
        frappe.throw("Agriculture Project Type must be an active Agriculture Project Type record.")

    context = _get_managed_item_context(project_type.farm_type, project_type)
    if not doc.get("farm"):
        frappe.throw("Farm is required for an Agriculture Project.")
    farm = get_farm_context(doc.farm)
    validate_farm_type_assignment(doc.farm, project_type.farm_type)
    if doc.get("company") and doc.company != farm.owner_name:
        frappe.throw("Project Company must match the Farm Owner Company.")
    doc.company = farm.owner_name
    doc.managed_item_doctype = context["doctype"]
    if context["default"] and not doc.get("managed_crop_animal_species"):
        doc.managed_crop_animal_species = context["default"]
    managed_item = doc.get("managed_crop_animal_species")
    if not managed_item:
        frappe.throw("Select the crop, animal, or species managed by this Project.")
    if managed_item not in context["options"]:
        choices = ", ".join(context["options"]) or "none configured"
        frappe.throw(
            f"{managed_item} is not valid for Agriculture Project Type {project_type.name}. "
            f"Select one of: {choices}."
        )
    validate_project_breed(context["doctype"], managed_item, doc.get("animal_breed"))
    output_item = get_project_output_item(project_type, managed_item)
    if not output_item:
        frappe.throw(
            f"No output Item is configured for {managed_item} under {project_type.name}. "
            "Configure it on the Agriculture Project Type or Farm Type."
        )
    doc.expected_output_item = output_item

    if flt(doc.get("project_quantity")) <= 0:
        frappe.throw("Project Quantity must be greater than zero.")
    if not doc.get("project_unit"):
        frappe.throw("Project Unit is required.")
    validate_date_order(
        doc.get("expected_start_date"),
        doc.get("expected_end_date"),
        "Expected Start Date",
        "Expected End Date",
    )


def sync_biological_asset_for_project(doc, method=None):
    if not doc.get("agriculture_project_type") or not doc.get("farm"):
        return

    if doc.get("biological_asset") and frappe.db.exists("Biological Asset", doc.biological_asset):
        profile = get_project_asset_profile(doc)
        asset = frappe.db.get_value(
            "Biological Asset",
            doc.biological_asset,
            ["farm", "farm_type", "managed_item", "output_item"],
            as_dict=True,
        )
        expected = {
            "farm": doc.farm,
            "farm_type": profile["farm_type"],
            "managed_item": profile["managed_item"],
            "output_item": profile["output_item"],
        }
        conflicts = [
            fieldname
            for fieldname, value in expected.items()
            if asset.get(fieldname) and asset.get(fieldname) != value
        ]
        if conflicts:
            frappe.throw(
                "Farm, Project Type, managed produce, and output Item cannot be changed "
                "after the Project has created its Biological Asset. Close this Project "
                "and create a new one for a different enterprise."
            )
        if profile.get("output_item") and not asset.output_item:
            frappe.db.set_value(
                "Biological Asset",
                doc.biological_asset,
                "output_item",
                profile["output_item"],
                update_modified=False,
            )
        return

    profile = get_project_asset_profile(doc)
    if not profile:
        return

    existing = frappe.db.get_value(
        "Biological Asset",
        {"linked_project": doc.name, "status": ["!=", "Harvested"]},
        "name",
    )
    if existing:
        doc.db_set("biological_asset", existing, update_modified=False)
        return

    asset = frappe.new_doc("Biological Asset")
    asset.asset_name = f"{doc.project_name or doc.name} - {profile['managed_item']}"
    asset.farm = doc.farm
    asset.asset_category = profile["asset_category"]
    asset.farm_type = profile["farm_type"]
    asset.managed_item = profile["managed_item"]
    asset.output_item = profile["output_item"]
    asset.livestock_breed = doc.get("animal_breed")
    asset.linked_project = doc.name
    asset.status = "Active"
    asset.growth_stage = profile.get("growth_stage") or "Immature"
    asset.valuation_method = "Cost Accumulation"
    asset.acquisition_date = profile.get("acquisition_date") or today()
    opening_value = flt(profile.get("initial_cost"))
    if profile["asset_category"] == "Crops in Growth" or opening_value:
        asset.quantity = profile.get("quantity") or 1
    else:
        asset.quantity = 0
    asset.unit = profile.get("unit") or "Head"
    asset.initial_cost = profile["initial_cost"]
    asset.current_fair_value = profile["initial_cost"]
    if not opening_value:
        asset.flags.allow_zero_initial_cost = True
    asset.insert(ignore_permissions=True)
    doc.db_set("biological_asset", asset.name, update_modified=False)


def get_project_asset_profile(doc):
    project_type = get_agriculture_project_type(doc.get("agriculture_project_type"))
    if project_type:
        farm_type = project_type.farm_type
        farm_category = get_primary_farm_activity(farm_type) or farm_type
        managed_item = (
            doc.get("managed_crop_animal_species")
            or project_type.managed_item
            or project_type.project_type_name
        )
        quantity = flt(doc.get("project_quantity")) or 1
        return {
            "asset_category": get_asset_category_from_farm_type(farm_category),
            "farm_type": farm_type,
            "managed_item": managed_item,
            "output_item": get_project_output_item(project_type, managed_item),
            "quantity": quantity,
            "unit": doc.get("project_unit") or get_default_unit_from_farm_type(farm_category),
            "acquisition_date": doc.get("expected_start_date") or today(),
            "initial_cost": flt(doc.get("initial_asset_cost")),
        }

    return None


def get_agriculture_project_type(project_type):
    if project_type and frappe.db.exists(
        "Agriculture Project Type", {"name": project_type, "is_active": 1}
    ):
        return frappe.get_doc("Agriculture Project Type", project_type)
    return None


@frappe.whitelist()
def get_managed_item_options(farm_type):
    """Return active managed masters for a Farm Type in deterministic order."""
    if not farm_type or not frappe.db.exists("Farm Type", farm_type):
        return []
    return _get_managed_item_context(farm_type)["options"]


@frappe.whitelist()
def get_project_managed_item_context(project_type):
    profile = get_agriculture_project_type(project_type)
    if not profile:
        frappe.throw("Select an active Agriculture Project Type.")
    context = _get_managed_item_context(profile.farm_type, profile)
    context["farm_type"] = profile.farm_type
    context["default_project_unit"] = get_default_unit_from_farm_type(
        get_primary_farm_activity(profile.farm_type)
    )
    context["output_items"] = {
        managed_item: get_project_output_item(profile, managed_item)
        for managed_item in context["options"]
    }
    return context


def get_project_output_item(project_type, managed_item):
    if project_type and project_type.output_item:
        return project_type.output_item
    return frappe.db.get_value(
        "Farm Type Managed Item",
        {
            "parent": project_type.farm_type if project_type else "",
            "parenttype": "Farm Type",
            "farm_produce": managed_item,
        },
        "default_output_item",
    )


def _get_managed_item_context(farm_type, project_type=None):
    if not farm_type or not frappe.db.exists("Farm Type", farm_type):
        return {"doctype": None, "options": [], "default": None}

    farm_type_doc = frappe.get_doc("Farm Type", farm_type)
    if not (frappe.flags.in_install or frappe.flags.in_migrate):
        farm_type_doc.check_permission("read")

    rows = [
        row
        for row in farm_type_doc.get("managed_items", [])
        if row.farm_produce and row.farm_produce_doctype
    ]
    if not rows:
        frappe.throw(
            f"Farm Type {farm_type} has no Farm Produce configured. "
            "Add produce rows or choose a more specific Agriculture Project Type."
        )
    default = project_type.managed_item if project_type else None
    if default:
        rows = [row for row in rows if row.farm_produce == default]
        if not rows:
            frappe.throw(
                f"{default} is not configured as Farm Produce on Farm Type {farm_type}."
            )

    doctypes = {row.farm_produce_doctype for row in rows}
    if len(doctypes) > 1:
        frappe.throw(
            f"Farm Type {farm_type} mixes crops and animal species. "
            "Use a specific Agriculture Project Type with a default Farm Produce."
        )
    produce_doctype = next(iter(doctypes), None)
    options = list(dict.fromkeys(row.farm_produce.strip() for row in rows))
    if produce_doctype == "Livestock Species":
        active = set(
            frappe.get_all(
                "Livestock Species",
                filters={"name": ["in", options], "is_active": 1},
                pluck="name",
            )
        )
        options = [name for name in options if name in active]

    return {
        "doctype": produce_doctype,
        "options": options,
        "default": default if default in options else None,
    }


def validate_managed_item(farm_type, managed_item):
    if not managed_item:
        return
    options = get_managed_item_options(farm_type)
    if options and managed_item not in options:
        frappe.throw(
            f"Managed Crop / Animal / Species must be selected from the active items on Farm Type {farm_type}."
        )


def validate_project_breed(produce_doctype, managed_item, breed):
    if not breed:
        return
    if produce_doctype != "Livestock Species":
        frappe.throw("Breed can only be selected for an animal or poultry Project.")
    breed_species = frappe.db.get_value(
        "Livestock Breed",
        {"name": breed, "is_active": 1},
        "species",
    )
    if not breed_species:
        frappe.throw("Select an active Livestock Breed.")
    if breed_species != managed_item:
        frappe.throw(f"Breed {breed} belongs to {breed_species}, not {managed_item}.")


def get_asset_category_from_farm_type(farm_category):
    if farm_category in ("Crop Production", "Horticulture", "Agroforestry"):
        return "Crops in Growth"
    if farm_category in ("Poultry", "Poultry Production"):
        return "Poultry"
    return "Livestock"


def get_primary_farm_activity(farm_type):
    return frappe.db.get_value(
        "Farm Type Managed Item",
        {"parent": farm_type, "parenttype": "Farm Type"},
        "farm_activity",
        order_by="idx asc",
    )


def get_default_unit_from_farm_type(farm_category):
    if farm_category in ("Poultry", "Poultry Production"):
        return "Bird"
    if farm_category in ("Crop Production", "Horticulture", "Agroforestry"):
        return "Hectare"
    if farm_category == "Apiculture":
        return "Colony"
    return "Head"
