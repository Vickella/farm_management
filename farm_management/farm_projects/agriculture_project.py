import frappe


def validate_agriculture_project(doc, method=None):
    if doc.get("agriculture_project_type") == "Crop Production":
        if not doc.get("crop_variety"):
            frappe.throw("Crop Variety is required for Crop Production projects.")
        if not doc.get("planting_date"):
            frappe.throw("Planting Date is required for Crop Production projects.")
        if (
            doc.get("harvest_date")
            and doc.get("planting_date")
            and doc.harvest_date <= doc.planting_date
        ):
            frappe.throw("Expected Harvest Date must be after Planting Date.")


def on_project_submit(doc, method=None):
    generate_farm_bom_from_project(doc)


def generate_farm_bom_from_project(project):
    return None
