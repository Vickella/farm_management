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
    return {
        "installed_apps": sorted(required_apps),
        "companies": companies,
        "reconciliation_rows": sum(len(rows) for rows in reconciliation.values()),
        "mismatches": mismatches,
        "missing_output_items": missing_output_items,
        "unmapped_farm_produce": unmapped_farm_produce,
        "unmapped_assets": unmapped_assets,
        "status": (
            "passed"
            if not (
                mismatches
                or missing_output_items
                or unmapped_farm_produce
                or unmapped_assets
            )
            else "blocked"
        ),
    }
