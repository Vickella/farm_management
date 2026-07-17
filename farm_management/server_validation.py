import frappe
from frappe.utils import flt, getdate


def get_farm_context(farm, require_active=True):
    context = frappe.db.get_value(
        "Farm",
        farm,
        ["name", "owner_name", "operational_status", "total_land_size"],
        as_dict=True,
    )
    if not context:
        frappe.throw("Select a valid Farm.")
    if require_active and context.operational_status != "Active":
        frappe.throw(f"Farm {farm} must be Active for operational transactions.")
    return context


def get_project_context(project, require_agriculture=True):
    context = frappe.db.get_value(
        "Project",
        project,
        [
            "name",
            "company",
            "farm",
            "agriculture_project_type",
            "managed_crop_animal_species",
            "managed_item_doctype",
            "animal_breed",
            "project_quantity",
            "project_unit",
            "biological_asset",
            "expected_start_date",
            "expected_end_date",
            "status",
        ],
        as_dict=True,
    )
    if not context:
        frappe.throw("Select a valid Project.")
    if require_agriculture and not context.agriculture_project_type:
        frappe.throw(f"Project {project} must be an Agriculture Project.")
    return context


def validate_farm_type_assignment(farm, farm_type):
    if not frappe.db.exists(
        "Farm Type Multiselect",
        {
            "parent": farm,
            "parenttype": "Farm",
            "parentfield": "farm_type",
            "farm_type": farm_type,
        },
    ):
        frappe.throw(f"Farm Type {farm_type} is not enabled on Farm {farm}.")


def apply_project_context(doc, require_asset=False):
    if not doc.get("project"):
        return None
    project = get_project_context(doc.project)
    if doc.get("farm") and project.farm and doc.farm != project.farm:
        frappe.throw(f"Farm must match Project {doc.project} farm {project.farm}.")
    if project.farm:
        doc.farm = project.farm
        farm = get_farm_context(project.farm)
        if project.company and farm.owner_name != project.company:
            frappe.throw(
                f"Project {doc.project} company must match Farm {project.farm} company."
            )
    if require_asset and not project.biological_asset:
        frappe.throw(f"Project {doc.project} has no Biological Asset.")
    return project


def validate_asset_context(asset_name, farm=None, project=None, active=False):
    asset = frappe.db.get_value(
        "Biological Asset",
        asset_name,
        [
            "name",
            "farm",
            "linked_project",
            "status",
            "asset_category",
            "managed_item",
            "livestock_breed",
            "quantity",
            "unit",
            "acquisition_date",
        ],
        as_dict=True,
    )
    if not asset:
        frappe.throw("Select a valid Biological Asset.")
    if active and asset.status != "Active":
        frappe.throw(f"Biological Asset {asset_name} must be Active.")
    if farm and asset.farm != farm:
        frappe.throw(f"Biological Asset {asset_name} must belong to Farm {farm}.")
    if project and asset.linked_project and asset.linked_project != project:
        frappe.throw(f"Biological Asset {asset_name} must belong to Project {project}.")
    return asset


def validate_date_order(start, end, start_label, end_label):
    if start and end and getdate(end) < getdate(start):
        frappe.throw(f"{end_label} cannot be before {start_label}.")


def validate_non_negative(doc, fieldnames):
    for fieldname in fieldnames:
        value = doc.get(fieldname)
        if value is not None and flt(value) < 0:
            frappe.throw(f"{doc.meta.get_label(fieldname)} cannot be negative.")


def validate_unique_rows(rows, fieldnames, label):
    seen = set()
    for row in rows:
        key = tuple(row.get(fieldname) for fieldname in fieldnames)
        if not any(key):
            continue
        if key in seen:
            frappe.throw(f"{label} is duplicated on row {row.idx}.")
        seen.add(key)
