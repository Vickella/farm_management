import frappe
from frappe.utils import flt
from frappe.utils import today

from farm_management.biological_assets.valuation import get_biological_asset_gl_reconciliation
from farm_management.install import (
    FARM_OUTPUT_ITEMS,
    configure_farm_output_items,
    link_managed_produce_masters_to_farm_types,
    seed_fixture_data,
    seed_livestock_breeds,
    seed_missing_crop_types,
)


def run():
    """Bench-executable verification for install, schema, and IAS 41 query paths."""
    installed_apps = set(frappe.get_installed_apps())
    required_apps = {"frappe", "erpnext", "farm_management"}
    missing_apps = required_apps - installed_apps
    if missing_apps:
        frappe.throw(f"Missing required apps: {', '.join(sorted(missing_apps))}")

    fixture_module_issues = []
    for module_name in {"Farm Setup"}:
        if not frappe.db.exists("Module Def", module_name):
            fixture_module_issues.append(module_name)

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

    project_meta = frappe.get_meta("Project")
    for fieldname in (
        "opening_quantity",
        "opening_unit_rate",
        "opening_recognition_date",
        "opening_stock_entry",
        "create_opening_stock_entry",
    ):
        if not project_meta.has_field(fieldname):
            frappe.throw(f"Project is missing central onboarding field: {fieldname}")

    harvest_meta = frappe.get_meta("Harvest Log")
    for fieldname in ("harvest_completion", "remaining_crop_fair_value"):
        if not harvest_meta.has_field(fieldname):
            frappe.throw(f"Harvest Log is missing crop lifecycle field: {fieldname}")

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
    managed_master_link_issues = []
    for row in frappe.get_all(
        "Farm Type Managed Item",
        filters={
            "parent": ["in", active_farm_types],
            "farm_produce": ["is", "set"],
            "farm_produce_doctype": ["in", ["Crop Type", "Livestock Species"]],
        },
        fields=["parent", "farm_produce_doctype", "farm_produce"],
    ):
        parent_field = (
            "category" if row.farm_produce_doctype == "Crop Type" else "farm_type"
        )
        linked_parent = frappe.db.get_value(
            row.farm_produce_doctype, row.farm_produce, parent_field
        )
        if linked_parent != row.parent:
            managed_master_link_issues.append(
                {
                    "farm_type": row.parent,
                    "produce_doctype": row.farm_produce_doctype,
                    "produce": row.farm_produce,
                    "linked_parent": linked_parent,
                }
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
            "create_opening_stock_entry",
            "opening_quantity",
            "opening_unit_rate",
            "opening_recognition_date",
            "opening_stock_entry",
            "project_quantity",
            "project_unit",
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
            elif project.managed_item_doctype == "Crop Type":
                asset_state = frappe.db.get_value(
                    "Biological Asset",
                    project.biological_asset,
                    ["status", "quantity", "unit", "asset_category"],
                    as_dict=True,
                )
                if asset_state.asset_category != "Crops in Growth":
                    reasons.append("crop Project points to a non-crop Biological Asset")
                elif asset_state.status == "Active" and (
                    flt(asset_state.quantity) != flt(project.project_quantity)
                    or asset_state.unit != project.project_unit
                ):
                    reasons.append("active crop asset area differs from Project planning area")
        if project.managed_item_doctype == "Livestock Species":
            if project.create_opening_stock_entry and not project.opening_stock_entry:
                reasons.append("opening recognition enabled without Opening Animal Entry")
            if project.opening_stock_entry:
                opening_entry = frappe.db.get_value(
                    "Animal Stock Entry",
                    project.opening_stock_entry,
                    [
                        "project",
                        "biological_asset",
                        "entry_type",
                        "docstatus",
                        "quantity",
                        "rate",
                        "posting_date",
                    ],
                    as_dict=True,
                )
                if not opening_entry:
                    reasons.append("Opening Animal Entry link is broken")
                elif (
                    opening_entry.project != project.name
                    or opening_entry.biological_asset != project.biological_asset
                    or opening_entry.entry_type != "Opening"
                    or opening_entry.docstatus == 2
                ):
                    reasons.append("Opening Animal Entry context does not match Project")
                elif opening_entry.docstatus == 1 and (
                    flt(opening_entry.quantity) != flt(project.opening_quantity)
                    or flt(opening_entry.rate) != flt(project.opening_unit_rate)
                    or opening_entry.posting_date != project.opening_recognition_date
                ):
                    reasons.append("submitted opening evidence differs from Project summary")
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
    harvest_automation_issues = []
    for harvest in frappe.get_all(
        "Harvest Log",
        filters={"docstatus": 1},
        fields=[
            "name",
            "farm",
            "biological_asset",
            "conversion_item",
            "harvest_completion",
            "harvest_transaction",
        ],
    ):
        reasons = []
        if not harvest.harvest_transaction:
            reasons.append("missing generated Harvest Transaction")
        else:
            transaction = frappe.db.get_value(
                "Harvest Transaction",
                harvest.harvest_transaction,
                [
                    "docstatus",
                    "farm",
                    "biological_asset",
                    "conversion_item",
                    "source_harvest_log",
                    "stock_entry",
                    "final_harvest",
                ],
                as_dict=True,
            )
            if not transaction or transaction.docstatus != 1:
                reasons.append("generated Harvest Transaction is not submitted")
            elif (
                transaction.farm != harvest.farm
                or transaction.biological_asset != harvest.biological_asset
                or transaction.conversion_item != harvest.conversion_item
                or transaction.source_harvest_log != harvest.name
            ):
                reasons.append("generated Harvest Transaction context differs from Harvest Log")
            else:
                if not transaction.stock_entry or frappe.db.get_value(
                    "Stock Entry", transaction.stock_entry, "docstatus"
                ) != 1:
                    reasons.append("harvest did not create a submitted stock receipt")
                expected_final = harvest.harvest_completion != "Partial"
                if bool(transaction.final_harvest) != expected_final:
                    reasons.append("partial/final harvest lifecycle flag is inconsistent")
                asset_status = frappe.db.get_value(
                    "Biological Asset", harvest.biological_asset, "status"
                )
                if not expected_final and asset_status != "Active":
                    reasons.append("partial harvest incorrectly closed the crop asset")
        if reasons:
            harvest_automation_issues.append(
                {"harvest_log": harvest.name, "reasons": reasons}
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
    duplicate_project_openings = frappe.db.sql(
        """
        select project
        from `tabAnimal Stock Entry`
        where entry_type = 'Opening'
          and docstatus < 2
          and ifnull(project, '') != ''
        group by project
        having count(*) > 1
        """,
        pluck=True,
    )
    return {
        "installed_apps": sorted(required_apps),
        "fixture_module_issues": fixture_module_issues,
        "companies": companies,
        "reconciliation_rows": sum(len(rows) for rows in reconciliation.values()),
        "mismatches": mismatches,
        "reclassifications": reclassifications,
        "project_issues": project_issues,
        "project_form_metadata_issues": project_form_metadata_issues,
        "submitted_harvests_without_quantity": submitted_harvests_without_quantity,
        "harvest_automation_issues": harvest_automation_issues,
        "missing_output_items": missing_output_items,
        "missing_live_animal_items": missing_live_animal_items,
        "unmapped_farm_produce": unmapped_farm_produce,
        "managed_master_link_issues": managed_master_link_issues,
        "farm_types_without_produce": farm_types_without_produce,
        "unmapped_assets": unmapped_assets,
        "animal_entries_without_asset": animal_entries_without_asset,
        "inbound_entries_without_batch": inbound_entries_without_batch,
        "duplicate_project_assets": duplicate_project_assets,
        "duplicate_project_openings": duplicate_project_openings,
        "status": (
            "passed"
            if not (
                mismatches
                or fixture_module_issues
                or missing_output_items
                or missing_live_animal_items
                or unmapped_farm_produce
                or managed_master_link_issues
                or farm_types_without_produce
                or unmapped_assets
                or project_issues
                or project_form_metadata_issues
                or submitted_harvests_without_quantity
                or harvest_automation_issues
                or animal_entries_without_asset
                or inbound_entries_without_batch
                or duplicate_project_assets
                or duplicate_project_openings
            )
            else "blocked"
        ),
    }


def run_project_onboarding_transaction_test():
    """Create, verify, and roll back a complete livestock Project onboarding flow."""
    farm = frappe.db.get_value(
        "Farm Type Multiselect",
        {
            "parenttype": "Farm",
            "parentfield": "farm_type",
            "farm_type": "Animal Husbandry",
        },
        "parent",
    )
    if not farm:
        frappe.throw("No Farm configured for Animal Husbandry acceptance testing.")
    if not frappe.db.exists(
        "Agriculture Project Type", {"name": "Pig Farming", "is_active": 1}
    ):
        frappe.throw("Active Pig Farming Project Type is required for acceptance testing.")

    try:
        project = frappe.new_doc("Project")
        project.project_name = f"ROLLBACK Livestock Onboarding {frappe.generate_hash(length=8)}"
        project.status = "Open"
        project.expected_start_date = today()
        project.agriculture_project_type = "Pig Farming"
        project.managed_item_doctype = "Livestock Species"
        project.managed_crop_animal_species = "Pigs"
        project.animal_breed = "Duroc"
        project.project_quantity = 12
        project.project_unit = "Head"
        project.farm = farm
        project.create_opening_stock_entry = 1
        project.opening_quantity = 10
        project.opening_unit_rate = 25
        project.opening_recognition_date = today()
        project.insert(ignore_permissions=True)

        project.reload()
        if not project.biological_asset or not project.opening_stock_entry:
            frappe.throw("Project did not create both required onboarding records.")
        asset = frappe.get_doc("Biological Asset", project.biological_asset)
        opening = frappe.get_doc("Animal Stock Entry", project.opening_stock_entry)
        if flt(asset.quantity):
            frappe.throw("Draft onboarding incorrectly recognized asset quantity.")
        if asset.linked_project != project.name or asset.managed_item != "Pigs":
            frappe.throw("Generated Biological Asset context is incorrect.")
        if (
            opening.docstatus != 0
            or opening.entry_type != "Opening"
            or opening.project != project.name
            or opening.biological_asset != asset.name
            or flt(opening.quantity) != 10
            or flt(opening.rate) != 25
            or opening.unit != "Head"
        ):
            frappe.throw("Generated Opening Animal Entry defaults are incorrect.")

        project.save(ignore_permissions=True)
        opening_count = frappe.db.count(
            "Animal Stock Entry",
            {
                "project": project.name,
                "entry_type": "Opening",
                "docstatus": ["<", 2],
            },
        )
        if opening_count != 1:
            frappe.throw("Repeated Project save created duplicate opening entries.")
        return {
            "status": "passed",
            "biological_asset_quantity_before_submit": asset.quantity,
            "opening_entry_docstatus": opening.docstatus,
            "opening_quantity": opening.quantity,
            "opening_rate": opening.rate,
            "duplicate_opening_count": opening_count,
            "rolled_back": True,
        }
    finally:
        frappe.db.rollback()


def run_crop_lifecycle_transaction_test():
    """Exercise Project, field planning, partial/final harvest, stock, and rollback."""
    project_type = "Crop Production"
    managed_crop = "Maize"
    farm_type = frappe.db.get_value(
        "Agriculture Project Type",
        {"name": project_type, "is_active": 1},
        "farm_type",
    )
    if not farm_type:
        frappe.throw("Active Crop Production Project Type is required for acceptance testing.")
    farm = frappe.db.get_value(
        "Farm Type Multiselect",
        {
            "parenttype": "Farm",
            "parentfield": "farm_type",
            "farm_type": farm_type,
        },
        "parent",
    )
    if not farm:
        frappe.throw(f"No Farm is configured for {farm_type} acceptance testing.")

    try:
        project = frappe.new_doc("Project")
        project.project_name = f"ROLLBACK Crop Lifecycle {frappe.generate_hash(length=8)}"
        project.status = "Open"
        project.expected_start_date = today()
        project.agriculture_project_type = project_type
        project.managed_item_doctype = "Crop Type"
        project.managed_crop_animal_species = managed_crop
        project.project_quantity = 2
        project.project_unit = "Hectare"
        project.farm = farm
        project.insert(ignore_permissions=True)
        project.reload()

        asset = frappe.get_doc("Biological Asset", project.biological_asset)
        if (
            asset.asset_category != "Crops in Growth"
            or asset.managed_item != managed_crop
            or flt(asset.quantity) != 2
            or asset.unit != "Hectare"
            or not asset.output_item
        ):
            frappe.throw("Project did not create the expected crop-in-growth asset context.")
        project.save(ignore_permissions=True)
        if frappe.db.count(
            "Biological Asset",
            {"linked_project": project.name, "status": "Active"},
        ) != 1:
            frappe.throw("Repeated crop Project save created duplicate active assets.")

        field_work = frappe.get_doc(
            {
                "doctype": "Field Management",
                "farm": farm,
                "project": project.name,
                "date": today(),
                "activity_type": "Weeding",
                "details": "Rollback-only crop lifecycle acceptance test",
                "requirements": [{"item": asset.output_item, "quantity": 1}],
            }
        )
        field_work.insert(ignore_permissions=True)
        field_work.submit()
        field_work.reload()
        if field_work.status != "Completed":
            frappe.throw("Submitted Field Management status did not become Completed.")

        valuation = frappe.get_doc(
            {
                "doctype": "Biological Asset Valuation",
                "biological_asset": asset.name,
                "valuation_date": today(),
                "valuation_method": "Manual Fair Value",
                "current_fair_value": 150,
                "cost_to_sell": 0,
                "valuation_basis": "Rollback-only crop lifecycle acceptance test",
                "post_journal_entry": 0,
            }
        )
        valuation.insert(ignore_permissions=True)
        valuation.submit()

        partial = frappe.get_doc(
            {
                "doctype": "Harvest Log",
                "farm": farm,
                "project": project.name,
                "date": today(),
                "harvested_quantity": 1,
                "harvest_fair_value": 50,
                "harvest_completion": "Partial",
                "remaining_crop_fair_value": 100,
            }
        )
        partial.insert(ignore_permissions=True)
        partial.submit()
        partial.reload()
        asset.reload()
        if (
            partial.status != "Completed"
            or not partial.harvest_transaction
            or asset.status != "Active"
            or flt(asset.quantity) != 2
            or abs(flt(asset.net_fair_value) - 100) > 0.01
        ):
            frappe.throw("Partial harvest did not preserve crop area and remaining value.")

        final = frappe.get_doc(
            {
                "doctype": "Harvest Log",
                "farm": farm,
                "project": project.name,
                "date": today(),
                "harvested_quantity": 2,
                "harvest_fair_value": 100,
                "harvest_completion": "Final",
            }
        )
        final.insert(ignore_permissions=True)
        final.submit()
        final.reload()
        asset.reload()
        transactions = frappe.get_all(
            "Harvest Transaction",
            filters={
                "source_harvest_log": ["in", [partial.name, final.name]],
                "docstatus": 1,
            },
            fields=["name", "stock_entry", "unit"],
        )
        if len(transactions) != 2 or any(
            not row.stock_entry
            or frappe.db.get_value("Stock Entry", row.stock_entry, "docstatus") != 1
            for row in transactions
        ):
            frappe.throw("Crop harvests did not create submitted stock receipts exactly once.")
        if asset.status != "Harvested" or flt(asset.quantity) or flt(asset.net_fair_value):
            frappe.throw("Final harvest did not close the crop Biological Asset.")

        return {
            "status": "passed",
            "project": project.name,
            "biological_asset": asset.name,
            "planning_quantity": project.project_quantity,
            "planning_uom": project.project_unit,
            "harvest_uom": transactions[0].unit,
            "partial_remaining_value": 100,
            "submitted_harvest_transactions": len(transactions),
            "final_asset_status": asset.status,
            "rolled_back": True,
        }
    finally:
        frappe.db.rollback()


def run_fresh_master_seed_transaction_test():
    """Reproduce fresh master seeding twice and roll back every change."""
    fixtures_dir = frappe.get_app_path("farm_management", "..", "fixtures")
    farm_type_path = f"{fixtures_dir}/farm_type.json"
    with open(farm_type_path, encoding="utf-8") as fixture_file:
        farm_type_records = frappe.parse_json(fixture_file.read())

    farm_types = [row["farm_type_name"] for row in farm_type_records]
    crop_names = {
        child["managed_item_name"]
        for row in farm_type_records
        for child in row.get("managed_items", [])
        if child.get("managed_item_type") in ("Crop", "Other")
    }
    species_names = {
        child["managed_item_name"]
        for row in farm_type_records
        for child in row.get("managed_items", [])
        if child.get("managed_item_type") in ("Animal Species", "Poultry", "Apiary")
    }
    previous_in_migrate = getattr(frappe.flags, "in_migrate", False)
    try:
        frappe.flags.in_migrate = True
        frappe.db.delete("Module Def", {"name": "Farm Setup"})
        from farm_management.install import ensure_module_defs

        ensure_module_defs()
        ensure_module_defs()
        if frappe.db.count("Module Def", {"name": "Farm Setup"}) != 1:
            frappe.throw("Required fixture Module Def was not created idempotently.")
        frappe.db.delete(
            "Farm Type Managed Item",
            {"parenttype": "Farm Type", "parent": ["in", farm_types]},
        )
        frappe.db.delete("Farm Type", {"name": ["in", farm_types]})
        frappe.db.delete("Crop Type", {"name": ["in", list(crop_names)]})
        frappe.db.delete(
            "Livestock Species", {"name": ["in", list(species_names)]}
        )

        def rebuild_and_validate():
            seed_missing_crop_types()
            seed_livestock_breeds()
            seed_fixture_data({"crop_type.json", "farm_type.json"})
            link_managed_produce_masters_to_farm_types()
            configure_farm_output_items()

            missing_farm_types = [
                name for name in farm_types if not frappe.db.exists("Farm Type", name)
            ]
            missing_crops = [
                name for name in crop_names if not frappe.db.exists("Crop Type", name)
            ]
            missing_species = [
                name
                for name in species_names
                if not frappe.db.exists("Livestock Species", name)
            ]
            link_issues = []
            for row in frappe.get_all(
                "Farm Type Managed Item",
                filters={"parent": ["in", farm_types], "parenttype": "Farm Type"},
                fields=["parent", "farm_produce_doctype", "farm_produce"],
            ):
                if not frappe.db.exists(row.farm_produce_doctype, row.farm_produce):
                    link_issues.append(f"{row.parent}: missing {row.farm_produce}")
                    continue
                parent_field = (
                    "category"
                    if row.farm_produce_doctype == "Crop Type"
                    else "farm_type"
                )
                if frappe.db.get_value(
                    row.farm_produce_doctype, row.farm_produce, parent_field
                ) != row.parent:
                    link_issues.append(f"{row.parent}: reverse link for {row.farm_produce}")
                if not row.farm_produce or not row.farm_produce_doctype:
                    link_issues.append(f"{row.parent}: incomplete managed produce row")
            if missing_farm_types or missing_crops or missing_species or link_issues:
                frappe.throw(
                    "Fresh master seed failed: "
                    + frappe.as_json(
                        {
                            "missing_farm_types": missing_farm_types,
                            "missing_crops": missing_crops,
                            "missing_species": missing_species,
                            "link_issues": link_issues,
                        }
                    )
                )
            return frappe.db.count(
                "Farm Type Managed Item",
                {"parent": ["in", farm_types], "parenttype": "Farm Type"},
            )

        first_row_count = rebuild_and_validate()
        second_row_count = rebuild_and_validate()
        if second_row_count != first_row_count:
            frappe.throw("Repeated master seed changed the managed produce row count.")
        return {
            "status": "passed",
            "farm_types": len(farm_types),
            "crops": len(crop_names),
            "species": len(species_names),
            "managed_produce_rows": second_row_count,
            "second_seed_duplicate_rows": second_row_count - first_row_count,
            "fixture_module_defs": 1,
            "rolled_back": True,
        }
    finally:
        frappe.flags.in_migrate = previous_in_migrate
        frappe.db.rollback()
