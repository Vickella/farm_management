import frappe
from frappe.utils import flt, today


def validate_agriculture_project(doc, method=None):
    ptype = doc.get("agriculture_project_type")
    if not ptype:
        return

    if ptype == "Crop Production":
        if not doc.get("crop_variety"):
            frappe.throw("Crop Variety is required for Crop Production projects.")
        if not doc.get("planting_date"):
            frappe.throw("Planting Date is required for Crop Production projects.")
        if doc.get("harvest_date") and doc.get("planting_date"):
            if doc.harvest_date <= doc.planting_date:
                frappe.throw("Harvest Date must be after Planting Date.")

    elif ptype == "Poultry Production":
        if not doc.get("poultry_breed"):
            frappe.throw("Breed is required for Poultry Production projects.")
        if not doc.get("chick_quantity") or int(doc.get("chick_quantity", 0)) <= 0:
            frappe.throw("Chick Quantity must be greater than zero.")

    elif ptype == "Fish Farming":
        if not doc.get("fish_species_managed_item") and not doc.get("fish_species"):
            frappe.throw("Fish Species is required for Fish Farming projects.")
        if not doc.get("fingerling_quantity") or int(doc.get("fingerling_quantity", 0)) <= 0:
            frappe.throw("Fingerling Quantity must be greater than zero.")

    elif ptype == "Dairy Production":
        if not doc.get("dairy_breed"):
            frappe.throw("Breed is required for Dairy Production projects.")

    elif ptype == "Goat Farming":
        if not doc.get("goat_breed"):
            frappe.throw("Breed is required for Goat Farming projects.")

    elif ptype == "Pig Farming":
        if not doc.get("pig_breed"):
            frappe.throw("Breed is required for Pig Farming projects.")


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
    project_type = doc.get("agriculture_project_type")
    if project_type == "Crop Production":
        managed_item = doc.get("crop_variety")
        return {
            "asset_category": "Crops in Growth",
            "farm_type": get_farm_type("Crop Production"),
            "managed_item": managed_item,
            "quantity": get_field_area(doc.get("field_allocation")) or 1,
            "unit": "Hectare",
            "acquisition_date": doc.get("planting_date"),
        } if managed_item else None

    if project_type == "Greenhouse Farming":
        managed_item = doc.get("greenhouse_crop")
        return {
            "asset_category": "Crops in Growth",
            "farm_type": get_farm_type("Horticulture") or get_farm_type("Crop Production"),
            "managed_item": managed_item,
            "quantity": flt(doc.get("greenhouse_area_sqm")) or 1,
            "unit": "Hectare",
            "acquisition_date": doc.get("planting_date_gh"),
        } if managed_item else None

    if project_type == "Poultry Production":
        return {
            "asset_category": "Poultry",
            "farm_type": get_farm_type("Poultry"),
            "managed_item": doc.get("poultry_breed") or "Poultry",
            "quantity": flt(doc.get("chick_quantity")) or 1,
            "unit": "Bird",
        }

    if project_type == "Fish Farming":
        return {
            "asset_category": "Aquaculture",
            "farm_type": doc.get("fish_species") or get_farm_type("Aquaculture"),
            "managed_item": doc.get("fish_species_managed_item") or "Aquaculture Stock",
            "quantity": flt(doc.get("fingerling_quantity")) or 1,
            "unit": "Fingerling",
            "acquisition_date": doc.get("stocking_date"),
        }

    livestock_profiles = {
        "Dairy Production": ("dairy_breed", "herd_size"),
        "Goat Farming": ("goat_breed", "goat_herd_size"),
        "Pig Farming": ("pig_breed", "pig_herd_size"),
    }
    if project_type in livestock_profiles:
        breed_field, quantity_field = livestock_profiles[project_type]
        return {
            "asset_category": "Livestock",
            "farm_type": get_farm_type("Animal Husbandry"),
            "managed_item": doc.get(breed_field) or project_type,
            "quantity": flt(doc.get(quantity_field)) or 1,
            "unit": "Head",
        }

    return None


def get_farm_type(category):
    return frappe.db.get_value("Farm Type", {"category": category, "is_active": 1}, "name")


def get_field_area(field_allocation):
    if not field_allocation:
        return 0
    return flt(frappe.db.get_value("Farm Field", field_allocation, "field_size_ha"))
