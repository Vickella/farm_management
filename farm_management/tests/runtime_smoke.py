import frappe

from farm_management.biological_assets.valuation import get_biological_asset_gl_reconciliation
from farm_management.install import FARM_OUTPUT_ITEMS


def run():
    """Bench-executable verification for install, schema, and IAS 41 query paths."""
    installed_apps = set(frappe.get_installed_apps())
    required_apps = {"frappe", "erpnext", "farm_management"}
    missing_apps = required_apps - installed_apps
    if missing_apps:
        frappe.throw(f"Missing required apps: {', '.join(sorted(missing_apps))}")

    animal_entry = frappe.get_meta("Animal Stock Entry")
    for fieldname in (
        "purchase_invoice",
        "sales_invoice",
        "purchase_expense_account",
        "asset_value_reduction",
    ):
        if not animal_entry.has_field(fieldname):
            frappe.throw(f"Animal Stock Entry is missing field: {fieldname}")

    for doctype, fieldname in (
        ("Project", "expected_output_item"),
        ("Biological Asset", "output_item"),
        ("Agriculture Project Type", "output_item"),
        ("Farm Type Managed Item", "default_output_item"),
    ):
        if not frappe.get_meta(doctype).has_field(fieldname):
            frappe.throw(f"{doctype} is missing output relationship field: {fieldname}")

    missing_output_items = [
        item_code
        for item_code in FARM_OUTPUT_ITEMS
        if not frappe.db.exists("Item", item_code)
    ]
    unmapped_farm_produce = frappe.get_all(
        "Farm Type Managed Item",
        filters={
            "farm_produce": ["is", "set"],
            "default_output_item": ["is", "not set"],
        },
        fields=["parent", "farm_produce"],
    )
    farm_types_without_produce = [
        farm_type
        for farm_type in frappe.get_all(
            "Farm Type",
            filters={"is_active": 1, "name": ["!=", "Mixed Farming"]},
            pluck="name",
        )
        if not frappe.db.exists(
            "Farm Type Managed Item",
            {
                "parent": farm_type,
                "parenttype": "Farm Type",
                "farm_produce": ["is", "set"],
                "farm_produce_doctype": ["is", "set"],
                "default_output_item": ["is", "set"],
            },
        )
    ]
    unmapped_assets = frappe.get_all(
        "Biological Asset",
        filters={"output_item": ["is", "not set"]},
        pluck="name",
    )

    for doctype in (
        "Biological Asset",
        "Biological Asset Capitalization",
        "Harvest Transaction",
        "Harvest Log",
        "Animal Stock Entry",
        "Farm Activity",
    ):
        if not frappe.db.exists("DocType", doctype):
            frappe.throw(f"Missing DocType after installation: {doctype}")

    companies = sorted(set(frappe.get_all("Farm", pluck="owner_name")) - {None, ""})
    if not companies:
        fallback_company = frappe.db.get_value("Company", {}, "name")
        companies = [fallback_company] if fallback_company else []
    reconciliation = {
        company: get_biological_asset_gl_reconciliation(company=company)
        for company in companies
    }
    mismatches = [
        {"company": company, **row}
        for company, rows in reconciliation.items()
        for row in rows
        if row["status"] == "Mismatch"
    ]
    reclassifications = [
        {"company": company, **row}
        for company, rows in reconciliation.items()
        for row in rows
        if row["status"] == "Reclassification Required"
    ]
    project_issues = []
    for project in frappe.get_all(
        "Project",
        filters={"agriculture_project_type": ["is", "set"]},
        fields=[
            "name",
            "farm",
            "agriculture_project_type",
            "agriculture_farm_type",
            "managed_item_doctype",
            "managed_crop_animal_species",
        ],
    ):
        project_type = frappe.db.get_value(
            "Agriculture Project Type",
            project.agriculture_project_type,
            ["farm_type", "is_active"],
            as_dict=True,
        )
        reasons = []
        if not project_type or not project_type.is_active:
            reasons.append("inactive or missing Project Type")
        if not project.managed_item_doctype or not project.managed_crop_animal_species:
            reasons.append("missing managed produce context")
        if project_type and project.farm and not frappe.db.exists(
            "Farm Type Multiselect",
            {
                "parent": project.farm,
                "parenttype": "Farm",
                "parentfield": "farm_type",
                "farm_type": project_type.farm_type,
            },
        ):
            reasons.append("Farm Type not enabled on Farm")
        if reasons:
            project_issues.append({"project": project.name, "reasons": reasons})

    submitted_harvests_without_quantity = frappe.get_all(
        "Harvest Log",
        filters={"docstatus": 1, "harvested_quantity": ["<=", 0]},
        pluck="name",
    )
    return {
        "installed_apps": sorted(required_apps),
        "companies": companies,
        "reconciliation_rows": sum(len(rows) for rows in reconciliation.values()),
        "mismatches": mismatches,
        "reclassifications": reclassifications,
        "project_issues": project_issues,
        "submitted_harvests_without_quantity": submitted_harvests_without_quantity,
        "missing_output_items": missing_output_items,
        "unmapped_farm_produce": unmapped_farm_produce,
        "farm_types_without_produce": farm_types_without_produce,
        "unmapped_assets": unmapped_assets,
        "status": (
            "passed"
            if not (
                mismatches
                or missing_output_items
                or unmapped_farm_produce
                or farm_types_without_produce
                or unmapped_assets
                or project_issues
                or submitted_harvests_without_quantity
            )
            else "blocked"
        ),
    }
