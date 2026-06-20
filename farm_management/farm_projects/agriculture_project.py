import frappe


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
