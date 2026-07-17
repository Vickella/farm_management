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

    project_form_metadata_issues = []
    agriculture_section = frappe.db.get_value(
        "Custom Field",
        {"dt": "Project", "fieldname": "section_break_agriculture_details"},
        ["name", "hidden", "depends_on"],
        as_dict=True,
    )
    if not agriculture_section:
        project_form_metadata_issues.append("Agriculture Details section is missing")
    elif agriculture_section.hidden or agriculture_section.depends_on:
        project_form_metadata_issues.append(
            "Agriculture Details section is hidden by stale metadata"
        )
    initial_cost_field = frappe.db.get_value(
        "Custom Field",
        {"dt": "Project", "fieldname": "initial_asset_cost"},
        ["name", "mandatory_depends_on"],
        as_dict=True,
    )
    if initial_cost_field and initial_cost_field.mandatory_depends_on:
        project_form_metadata_issues.append(
            "Opening Biological Asset Value is incorrectly mandatory"
        )

    animal_entry = frappe.get_meta("Animal Stock Entry")
    for fieldname in (
        "purchase_invoice",
        "sales_invoice",
        "purchase_expense_account",
        "asset_value_reduction",
        "batch_reference",
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
    active_farm_types = frappe.get_all(
        "Farm Type", filters={"is_active": 1}, pluck="name"
    )
    unmapped_farm_produce = frappe.get_all(
        "Farm Type Managed Item",
        filters={
            "parent": ["in", active_farm_types],
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
    missing_live_animal_items = []
    for species in frappe.get_all(
        "Livestock Species",
        filters={"is_active": 1},
        fields=["name", "species_name"],
    ):
        key = frappe.scrub(species.species_name or species.name).upper().replace("_", "-")
        item_code = f"LIVE-ANIMAL-{key}"
        item = frappe.db.get_value(
            "Item", item_code, ["disabled", "is_stock_item"], as_dict=True
        )
        if not item or item.disabled or item.is_stock_item:
            missing_live_animal_items.append(item_code)

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
            "biological_asset",
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
        if not project.biological_asset:
            reasons.append("missing Biological Asset")
        else:
            asset = frappe.db.get_value(
                "Biological Asset",
                project.biological_asset,
                ["linked_project", "farm", "managed_item"],
                as_dict=True,
            )
            if not asset:
                reasons.append("linked Biological Asset does not exist")
            elif (
                asset.linked_project != project.name
                or asset.farm != project.farm
                or asset.managed_item != project.managed_crop_animal_species
            ):
                reasons.append("Biological Asset context does not match Project")
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
    animal_entries_without_asset = frappe.get_all(
        "Animal Stock Entry",
        filters={"docstatus": ["<", 2], "biological_asset": ["is", "not set"]},
        pluck="name",
    )
    inbound_entries_without_batch = frappe.get_all(
        "Animal Stock Entry",
        filters={
            "docstatus": 1,
            "entry_type": ["in", ["Opening", "Receipt", "Purchase", "Birth"]],
            "batch_reference": ["is", "not set"],
        },
        pluck="name",
    )
    duplicate_project_assets = frappe.db.sql(
        """
        select linked_project
        from `tabBiological Asset`
        where status = 'Active' and ifnull(linked_project, '') != ''
        group by linked_project
        having count(*) > 1
        """,
        pluck=True,
    )
    return {
        "installed_apps": sorted(required_apps),
        "companies": companies,
        "reconciliation_rows": sum(len(rows) for rows in reconciliation.values()),
        "mismatches": mismatches,
        "reclassifications": reclassifications,
        "project_issues": project_issues,
        "project_form_metadata_issues": project_form_metadata_issues,
        "submitted_harvests_without_quantity": submitted_harvests_without_quantity,
        "missing_output_items": missing_output_items,
        "missing_live_animal_items": missing_live_animal_items,
        "unmapped_farm_produce": unmapped_farm_produce,
        "farm_types_without_produce": farm_types_without_produce,
        "unmapped_assets": unmapped_assets,
        "animal_entries_without_asset": animal_entries_without_asset,
        "inbound_entries_without_batch": inbound_entries_without_batch,
        "duplicate_project_assets": duplicate_project_assets,
        "status": (
            "passed"
            if not (
                mismatches
                or missing_output_items
                or missing_live_animal_items
                or unmapped_farm_produce
                or farm_types_without_produce
                or unmapped_assets
                or project_issues
                or project_form_metadata_issues
                or submitted_harvests_without_quantity
                or animal_entries_without_asset
                or inbound_entries_without_batch
                or duplicate_project_assets
            )
            else "blocked"
        ),
    }
