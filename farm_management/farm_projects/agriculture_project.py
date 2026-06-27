import frappe
from frappe.utils import flt, today


def validate_agriculture_project(doc, method=None):
    ptype = doc.get("agriculture_project_type")
    if not ptype:
        return
    project_type = get_agriculture_project_type(ptype)
    if project_type:
        doc.agriculture_farm_type = project_type.farm_type
        if project_type.managed_item and not doc.get("managed_crop_animal_species"):
            doc.managed_crop_animal_species = project_type.managed_item
    else:
        frappe.throw("Agriculture Project Type must be an active Agriculture Project Type record.")

    if doc.get("project_quantity") and flt(doc.get("project_quantity")) < 0:
        frappe.throw("Project Quantity cannot be negative.")


def on_project_submit(doc, method=None):
    generate_farm_bom_from_project(doc)


def generate_farm_bom_from_project(project):
    return None


def sync_biological_asset_for_project(doc, method=None):
    if not doc.get("agriculture_project_type") or not doc.get("farm"):
        return

    if doc.get("biological_asset") and frappe.db.exists("Biological Asset", doc.biological_asset):
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
    asset.linked_project = doc.name
    asset.status = "Active"
    asset.growth_stage = profile.get("growth_stage") or "Immature"
    asset.valuation_method = "Cost Accumulation"
    asset.acquisition_date = profile.get("acquisition_date") or today()
    asset.quantity = profile.get("quantity") or 1
    asset.unit = profile.get("unit") or "Head"
    asset.initial_cost = 0
    asset.current_fair_value = 0
    asset.insert(ignore_permissions=True)
    doc.db_set("biological_asset", asset.name, update_modified=False)


def get_project_asset_profile(doc):
    project_type = get_agriculture_project_type(doc.get("agriculture_project_type"))
    if project_type:
        farm_type = project_type.farm_type
        farm_category = frappe.db.get_value("Farm Type", farm_type, "category") or farm_type
        managed_item = (
            doc.get("managed_crop_animal_species")
            or project_type.managed_item
            or get_legacy_managed_item(doc)
            or project_type.project_type_name
        )
        quantity = flt(doc.get("project_quantity")) or get_legacy_quantity(doc) or 1
        return {
            "asset_category": get_asset_category_from_farm_type(farm_category),
            "farm_type": farm_type,
            "managed_item": managed_item,
            "quantity": quantity,
            "unit": doc.get("project_unit") or get_default_unit_from_farm_type(farm_category),
            "acquisition_date": get_legacy_acquisition_date(doc),
        }

    return None


def get_agriculture_project_type(project_type):
    if project_type and frappe.db.exists("Agriculture Project Type", project_type):
        return frappe.get_doc("Agriculture Project Type", project_type)
    return None


def get_asset_category_from_farm_type(farm_category):
    if farm_category in ("Crop Production", "Horticulture", "Agroforestry"):
        return "Crops in Growth"
    if farm_category == "Poultry":
        return "Poultry"
    if farm_category == "Aquaculture":
        return "Aquaculture"
    return "Livestock"


def get_default_unit_from_farm_type(farm_category):
    if farm_category == "Poultry":
        return "Bird"
    if farm_category == "Aquaculture":
        return "Fingerling"
    if farm_category in ("Crop Production", "Horticulture", "Agroforestry"):
        return "Hectare"
    if farm_category == "Apiculture":
        return "Colony"
    return "Head"


def get_legacy_managed_item(doc):
    return (
        doc.get("crop_variety")
        or doc.get("greenhouse_crop")
        or doc.get("fish_species_managed_item")
        or doc.get("poultry_breed")
        or doc.get("dairy_breed")
        or doc.get("goat_breed")
        or doc.get("pig_breed")
    )


def get_legacy_quantity(doc):
    return (
        get_field_area(doc.get("field_allocation"))
        or flt(doc.get("greenhouse_area_sqm"))
        or flt(doc.get("chick_quantity"))
        or flt(doc.get("fingerling_quantity"))
        or flt(doc.get("herd_size"))
        or flt(doc.get("goat_herd_size"))
        or flt(doc.get("pig_herd_size"))
    )


def get_legacy_acquisition_date(doc):
    return (
        doc.get("planting_date")
        or doc.get("planting_date_gh")
        or doc.get("stocking_date")
        or doc.get("expected_start_date")
        or today()
    )


def get_farm_type(category):
    return frappe.db.get_value("Farm Type", {"category": category, "is_active": 1}, "name")


def get_field_area(field_allocation):
    if not field_allocation:
        return 0
    return flt(frappe.db.get_value("Farm Field", field_allocation, "field_size_ha"))
