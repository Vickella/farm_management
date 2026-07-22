import ast
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPO_ROOT / "farm_management"

RETAINED_DOCTYPES = {
    "Agriculture Project Type",
    "Animal Disease",
    "Animal Stock Entry",
    "Biological Asset",
    "Biological Asset Capitalization",
    "Biological Asset Valuation",
    "Crop Type",
    "Disease Incident",
    "Farm",
    "Farm Activity",
    "Farm Activity Type",
    "Farm BOM",
    "Farm BOM Item",
    "Farm Budget",
    "Farm Budget Item",
    "Farm Cashbook",
    "Farm Cashbook Entry",
    "Farm Field",
    "Farm Management Settings",
    "Farm Pen",
    "Farm Type",
    "Farm Type Managed Item",
    "Farm Type Multiselect",
    "Field Management",
    "Field Management Requirement",
    "Fowl Run",
    "Harvest Log",
    "Harvest Transaction",
    "Livestock Breed",
    "Livestock Breeding Record",
    "Livestock Health Event",
    "Livestock Individual",
    "Livestock Sibling",
    "Livestock Species",
    "Pest",
}


def get_doctype(name):
    for path in APP_ROOT.glob("**/doctype/**/*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("name") == name:
            return data
    raise AssertionError(f"DocType not found: {name}")


class TestRepositoryContracts(unittest.TestCase):
    def test_doctype_inventory_stays_minimal(self):
        present = {
            json.loads(path.read_text(encoding="utf-8")).get("name")
            for path in APP_ROOT.glob("**/doctype/**/*.json")
        }
        self.assertEqual(present, RETAINED_DOCTYPES)

    def test_all_doctype_json_and_field_order_are_valid(self):
        for path in APP_ROOT.glob("**/doctype/**/*.json"):
            with self.subTest(path=path):
                data = json.loads(path.read_text(encoding="utf-8"))
                fieldnames = [row.get("fieldname") for row in data.get("fields", [])]
                self.assertEqual(len(fieldnames), len(set(fieldnames)))
                self.assertEqual(set(data.get("field_order", [])), set(fieldnames))
                if data.get("is_submittable"):
                    self.assertIn("amended_from", fieldnames)
                for field in data.get("fields", []):
                    if field.get("fieldtype") in {"Table", "Table MultiSelect"}:
                        self.assertIn(field.get("options"), RETAINED_DOCTYPES)

    def test_erpnext_is_a_required_app(self):
        hooks = (APP_ROOT / "hooks.py").read_text(encoding="utf-8")
        self.assertIn('required_apps = ["erpnext"]', hooks)

    def test_transactional_bom_fixture_is_excluded(self):
        install = (APP_ROOT / "install.py").read_text(encoding="utf-8")
        self.assertIn('EXCLUDED_INSTALL_FIXTURES = {"farm_bom.json"}', install)
        self.assertLess(
            install.index('"crop_type.json"'), install.index('"farm_type.json"')
        )
        self.assertIn("link_managed_produce_masters_to_farm_types()", install)
        self.assertIn('record["category"] = None', install)
        runtime_smoke = (APP_ROOT / "tests" / "runtime_smoke.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("run_fresh_master_seed_transaction_test", runtime_smoke)
        self.assertIn("second_seed_duplicate_rows", runtime_smoke)

    def test_master_selection_fields_are_links(self):
        expected = {
            ("Farm Pen", "managed_species"): ("Link", "Livestock Species"),
            ("Fowl Run", "managed_species"): ("Link", "Livestock Species"),
        }
        for (doctype, fieldname), contract in expected.items():
            with self.subTest(doctype=doctype, fieldname=fieldname):
                field = next(
                    row
                    for row in get_doctype(doctype)["fields"]
                    if row.get("fieldname") == fieldname
                )
                self.assertEqual((field.get("fieldtype"), field.get("options")), contract)

    def test_project_produce_and_breed_are_category_constrained(self):
        fixtures = json.loads(
            (REPO_ROOT / "fixtures" / "custom_field.json").read_text(encoding="utf-8")
        )
        fields = {
            row["fieldname"]: row
            for row in fixtures
            if row.get("dt") == "Project"
        }
        self.assertEqual(
            (
                fields["managed_crop_animal_species"]["fieldtype"],
                fields["managed_crop_animal_species"]["options"],
            ),
            ("Dynamic Link", "managed_item_doctype"),
        )
        self.assertEqual(fields["animal_breed"]["options"], "Livestock Breed")

        controller = (
            APP_ROOT / "farm_projects" / "agriculture_project.py"
        ).read_text(encoding="utf-8")
        self.assertIn("get_project_managed_item_context", controller)
        self.assertIn("validate_project_breed", controller)
        self.assertIn("breed_species != managed_item", controller)

        client = (APP_ROOT / "public" / "js" / "project.js").read_text(encoding="utf-8")
        self.assertIn('name: ["in", produce]', client)
        self.assertIn("species: frm.doc.managed_crop_animal_species", client)

    def test_operational_units_use_uom_master(self):
        for doctype, fieldname in (
            ("Biological Asset", "unit"),
            ("Harvest Transaction", "unit"),
            ("Farm BOM", "planned_quantity_unit"),
            ("Crop Type", "yield_unit"),
            ("Animal Stock Entry", "unit"),
        ):
            with self.subTest(doctype=doctype, fieldname=fieldname):
                field = next(
                    row
                    for row in get_doctype(doctype)["fields"]
                    if row.get("fieldname") == fieldname
                )
                self.assertEqual(field.get("fieldtype"), "Link")
                self.assertEqual(field.get("options"), "UOM")

    def test_weather_feature_is_installed_and_configurable(self):
        weather = APP_ROOT / "farm_management" / "api" / "weather.py"
        page = APP_ROOT / "farm_setup" / "page" / "farm_weather"
        self.assertTrue(weather.is_file())
        self.assertTrue((page / "farm_weather.json").is_file())
        self.assertTrue((page / "farm_weather.js").is_file())
        self.assertNotIn("DEFAULT_OPENWEATHER_API_KEY", weather.read_text(encoding="utf-8"))

        settings = get_doctype("Farm Management Settings")
        fields = {field["fieldname"] for field in settings["fields"]}
        self.assertTrue({"weather_api_key", "weather_units"} <= fields)

        install = (APP_ROOT / "install.py").read_text(encoding="utf-8")
        self.assertNotIn('LEGACY_PAGES = ["agri-gpt", "farm-weather"]', install)
        self.assertIn('("Farm Weather", "Page", "farm-weather")', install)

    def test_farm_type_uses_activity_and_produce_rows(self):
        farm_type = get_doctype("Farm Type")
        self.assertNotIn("category", {field["fieldname"] for field in farm_type["fields"]})
        row = get_doctype("Farm Type Managed Item")
        fields = {field["fieldname"]: field for field in row["fields"]}
        self.assertEqual(fields["farm_activity"]["label"], "Farm Activity")
        self.assertEqual(fields["farm_produce"]["label"], "Farm Produce")
        self.assertEqual(fields["farm_produce"]["fieldtype"], "Dynamic Link")
        for legacy in (
            "managed_item_name",
            "managed_item_type",
            "crop_type",
            "livestock_species",
            "other_managed_item_name",
        ):
            self.assertNotIn(legacy, fields)

    def test_field_management_requirements_drive_estimate(self):
        field_management = get_doctype("Field Management")
        fields = {field["fieldname"]: field for field in field_management["fields"]}
        self.assertEqual(fields["details"]["label"], "Details")
        self.assertIn("Weeding", fields["activity_type"]["options"])
        self.assertEqual(fields["requirements"]["options"], "Field Management Requirement")
        self.assertTrue(fields["total_estimated_cost"]["read_only"])
        controller = (
            APP_ROOT / "crop_production" / "doctype" / "field_management" / "field_management.py"
        ).read_text(encoding="utf-8")
        self.assertIn("valuation_rate", controller)
        self.assertIn("estimated_amount", controller)

    def test_harvest_log_orchestrates_valuation_transaction_and_stock_uom(self):
        harvest = get_doctype("Harvest Log")
        fields = {field["fieldname"]: field for field in harvest["fields"]}
        self.assertEqual(fields["harvest_uom"]["options"], "UOM")
        self.assertEqual(fields["conversion_item"]["options"], "Item")
        self.assertEqual(fields["harvest_completion"]["options"], "Partial\nFinal")
        self.assertIn("mandatory_depends_on", fields["remaining_crop_fair_value"])
        controller = (
            APP_ROOT / "crop_production" / "doctype" / "harvest_log" / "harvest_log.py"
        ).read_text(encoding="utf-8")
        self.assertIn('"doctype": "Harvest Transaction"', controller)
        self.assertIn("transaction.submit()", controller)
        self.assertIn('"Biological Asset", self.biological_asset, "output_item"', controller)
        self.assertIn('"final_harvest"', controller)
        self.assertIn("target_net_fair_value", controller)
        transaction = get_doctype("Harvest Transaction")
        unit = next(field for field in transaction["fields"] if field["fieldname"] == "unit")
        self.assertNotIn("fetch_from", unit)
        transaction_controller = (
            APP_ROOT
            / "biological_assets"
            / "doctype"
            / "harvest_transaction"
            / "harvest_transaction.py"
        ).read_text(encoding="utf-8")
        self.assertIn("reduce_asset_value", transaction_controller)
        self.assertIn("self.final_harvest", transaction_controller)
        asset_controller = (
            APP_ROOT
            / "biological_assets"
            / "doctype"
            / "biological_asset"
            / "biological_asset.py"
        ).read_text(encoding="utf-8")
        self.assertIn("if self.is_new():", asset_controller)

    def test_every_seeded_farm_produce_has_a_preconfigured_output_item(self):
        source = (APP_ROOT / "install.py").read_text(encoding="utf-8")
        self.assertNotIn('has_column("tab', source)
        self.assertNotIn('table_exists("tab', source)
        module = ast.parse(source)
        constants = {}
        for statement in module.body:
            if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
                target = statement.targets[0]
                if isinstance(target, ast.Name) and target.id in {
                    "FARM_OUTPUT_ITEMS",
                    "DEFAULT_OUTPUT_ITEM_BY_PRODUCE",
                }:
                    constants[target.id] = ast.literal_eval(statement.value)

        farm_types = json.loads(
            (REPO_ROOT / "fixtures" / "farm_type.json").read_text(encoding="utf-8")
        )
        seeded_produce = {
            row["managed_item_name"]
            for farm_type in farm_types
            for row in farm_type.get("managed_items", [])
        }
        mappings = constants["DEFAULT_OUTPUT_ITEM_BY_PRODUCE"]
        self.assertEqual(seeded_produce, set(mappings))
        self.assertTrue(set(mappings.values()) <= set(constants["FARM_OUTPUT_ITEMS"]))
        self.assertIn("seed_farm_output_items()", source)
        self.assertIn("configure_farm_output_items()", source)

    def test_project_asset_and_harvest_share_the_output_item(self):
        project_fields = {
            row["fieldname"]: row
            for row in json.loads(
                (REPO_ROOT / "fixtures" / "custom_field.json").read_text(encoding="utf-8")
            )
            if row.get("dt") == "Project"
        }
        self.assertEqual(project_fields["expected_output_item"]["options"], "Item")
        asset_fields = {
            row["fieldname"]: row for row in get_doctype("Biological Asset")["fields"]
        }
        self.assertTrue(asset_fields["output_item"]["reqd"])
        self.assertEqual(asset_fields["output_item"]["options"], "Item")

        project_controller = (
            APP_ROOT / "farm_projects" / "agriculture_project.py"
        ).read_text(encoding="utf-8")
        self.assertIn('asset.output_item = profile["output_item"]', project_controller)
        self.assertIn('asset.initial_cost = profile["initial_cost"]', project_controller)
        self.assertNotIn("asset.initial_cost = 0", project_controller)
        self.assertIn("cannot be changed", project_controller)

        transaction = (
            APP_ROOT
            / "biological_assets"
            / "doctype"
            / "harvest_transaction"
            / "harvest_transaction.py"
        ).read_text(encoding="utf-8")
        self.assertIn("self.conversion_item != asset.output_item", transaction)

    def test_cancelable_doctypes_are_amendable_and_statuses_are_synchronized(self):
        for doctype in ("Biological Asset Valuation", "Biological Asset Capitalization"):
            fields = {field["fieldname"] for field in get_doctype(doctype)["fields"]}
            self.assertIn("amended_from", fields)
        hooks = (APP_ROOT / "hooks.py").read_text(encoding="utf-8")
        self.assertIn("sync_status_on_submit", hooks)
        self.assertNotIn('"*": {', hooks)
        install = (APP_ROOT / "install.py").read_text(encoding="utf-8")
        self.assertIn("ensure_amendable_doctypes", install)

    def test_operational_permissions_match_source_document_ownership(self):
        for doctype in ("Harvest Log", "Field Management", "Farm Cashbook"):
            permissions = {
                row["role"]: row for row in get_doctype(doctype)["permissions"]
            }
            farm_manager = permissions["Farm Manager"]
            self.assertTrue(farm_manager.get("create"))
            self.assertTrue(farm_manager.get("submit"))
            self.assertTrue(farm_manager.get("cancel"))
            self.assertTrue(farm_manager.get("amend"))

        for doctype in ("Harvest Log", "Field Management"):
            permissions = {
                row["role"]: row for row in get_doctype(doctype)["permissions"]
            }
            self.assertTrue(permissions["Farm Worker"].get("create"))
            self.assertFalse(permissions["Farm Worker"].get("submit", 0))

        for doctype in ("Biological Asset Capitalization", "Harvest Transaction"):
            permissions = {
                row["role"]: row for row in get_doctype(doctype)["permissions"]
            }
            self.assertTrue(permissions["Farm Manager"].get("read"))
            self.assertFalse(permissions["Farm Manager"].get("create", 0))
            self.assertTrue(permissions["Accounts Manager"].get("submit"))

    def test_source_document_statuses_are_system_driven(self):
        for doctype in (
            "Animal Stock Entry",
            "Field Management",
            "Harvest Log",
        ):
            fields = {
                row["fieldname"]: row for row in get_doctype(doctype)["fields"]
            }
            self.assertTrue(fields["status"].get("read_only"))

    def test_workspace_contains_core_farm_accounting_reports(self):
        install = (APP_ROOT / "install.py").read_text(encoding="utf-8")
        self.assertIn('"Profit and Loss Statement", "Report"', install)
        self.assertIn('"Accounts Receivable Summary", "Report"', install)
        self.assertIn('"Accounts Payable Summary", "Report"', install)
        self.assertNotIn('("Poultry Infrastructure", "DocType")', install)
        ias_section = install.split('"IAS 41 Biological Assets"', 1)[1].split("],", 1)[0]
        self.assertNotIn('"Biological Asset Capitalization"', ias_section)
        self.assertNotIn('"Harvest Transaction"', ias_section)
        for card in (
            "Farm Setup",
            "Field Operations",
            "Livestock Records",
            "IAS 41 Biological Assets",
            "Disease and Pest Intelligence",
            "Farm Accounting, Planning and Costing",
        ):
            self.assertIn(f'"{card}"', install)
        self.assertNotIn('"Farm Infrastructure"', install)
        self.assertNotIn('"Planning and Costing"', install)

    def test_project_is_the_contextual_operations_home(self):
        client = (APP_ROOT / "public" / "js" / "project.js").read_text(
            encoding="utf-8"
        )
        for label in (
            "Record Farm Activity",
            "Plan Inputs and Resources",
            "Record Field Work",
            "Harvest Crop",
            "Add Animal Group / Movement",
            "Add Individually Tracked Animal",
            "Record Valuation",
        ):
            self.assertIn(label, client)

        farm_client = (
            APP_ROOT / "farm_setup" / "doctype" / "farm" / "farm.js"
        ).read_text(encoding="utf-8")
        self.assertIn("View Weather Forecast", farm_client)

    def test_harvest_migration_repairs_generated_transaction_quantity(self):
        install = (APP_ROOT / "install.py").read_text(encoding="utf-8")
        self.assertIn("transaction.quantity_harvested", install)
        self.assertIn("repair_existing_project_contexts()", install)
        harvest = get_doctype("Harvest Log")
        fields = {row["fieldname"]: row for row in harvest["fields"]}
        self.assertTrue(fields["valuation_rate"].get("read_only"))
        smoke = (APP_ROOT / "tests" / "runtime_smoke.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("farm_types_without_produce", smoke)

    def test_live_animal_sales_and_purchases_require_standard_invoices(self):
        doc = get_doctype("Animal Stock Entry")
        fields = {row["fieldname"]: row for row in doc["fields"]}
        self.assertTrue(fields["project"].get("reqd"))
        self.assertTrue(fields["biological_asset"].get("read_only"))
        self.assertFalse(fields["biological_asset"].get("reqd", 0))
        self.assertTrue(fields["item"].get("read_only"))
        self.assertIn("batch_reference", fields)
        self.assertLess(
            doc["field_order"].index("project"),
            doc["field_order"].index("biological_asset"),
        )
        self.assertEqual(fields["purchase_invoice"].get("options"), "Purchase Invoice")
        self.assertEqual(fields["sales_invoice"].get("options"), "Sales Invoice")
        controller = (
            APP_ROOT / "livestock" / "doctype" / "animal_stock_entry" / "animal_stock_entry.py"
        ).read_text(encoding="utf-8")
        self.assertIn('invoice.docstatus != 1', controller)
        self.assertIn('invoice.get("is_return")', controller)
        self.assertIn("base_net_amount", controller)
        self.assertIn("self.set_project_defaults()", controller)
        self.assertIn("project.biological_asset", controller)
        self.assertIn("sync_biological_asset_for_project", controller)
        self.assertIn("get_or_create_live_animal_invoice_item", controller)
        self.assertIn('self.entry_type = "Receipt"', controller)
        self.assertIn('self.entry_type == "Opening"', controller)
        self.assertIn('"Opening", "Receipt", "Birth"', controller)
        client = (
            APP_ROOT / "livestock" / "doctype" / "animal_stock_entry" / "animal_stock_entry.js"
        ).read_text(encoding="utf-8")
        self.assertIn('managed_item_doctype: "Livestock Species"', client)
        self.assertIn('agriculture_project_type: ["is", "set"]', client)

        project_fields = {
            row["fieldname"]: row
            for row in json.loads(
                (REPO_ROOT / "fixtures" / "custom_field.json").read_text(encoding="utf-8")
            )
            if row.get("dt") == "Project"
        }
        self.assertFalse(
            project_fields["initial_asset_cost"].get("mandatory_depends_on")
        )
        self.assertFalse(
            project_fields["section_break_agriculture_details"].get("depends_on")
        )
        self.assertTrue(
            project_fields["project_quantity"].get("mandatory_depends_on")
        )
        self.assertTrue(project_fields["project_unit"].get("mandatory_depends_on"))
        for fieldname in (
            "opening_quantity",
            "opening_unit_rate",
            "opening_recognition_date",
            "opening_stock_entry",
            "create_opening_stock_entry",
        ):
            self.assertIn(fieldname, project_fields)
        install = (APP_ROOT / "install.py").read_text(encoding="utf-8")
        self.assertIn("optional_text_properties", install)
        self.assertIn('"mandatory_depends_on"', install)
        project_client = (APP_ROOT / "public" / "js" / "project.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("This is a general ERPNext Project", project_client)

        self.assertIn("seed_live_animal_invoice_items()", install)
        self.assertIn("repair_placeholder_livestock_asset_quantities()", install)
        self.assertIn("backfill_animal_stock_batch_references()", install)
        self.assertIn("backfill_project_opening_contexts()", install)

        smoke = (APP_ROOT / "tests" / "runtime_smoke.py").read_text(
            encoding="utf-8"
        )
        for diagnostic in (
            "missing_live_animal_items",
            "animal_entries_without_asset",
            "inbound_entries_without_batch",
            "duplicate_project_assets",
            "duplicate_project_openings",
            "project_form_metadata_issues",
        ):
            self.assertIn(diagnostic, smoke)
        self.assertIn("run_project_onboarding_transaction_test", smoke)
        self.assertIn("frappe.db.rollback()", smoke)

        hooks = (APP_ROOT / "hooks.py").read_text(encoding="utf-8")
        self.assertIn("sync_project_operational_records", hooks)
        self.assertNotIn(
            '"after_insert": "farm_management.farm_projects.agriculture_project.sync_biological_asset_for_project"',
            hooks,
        )

    def test_removed_feature_doctypes_do_not_return(self):
        removed = {
            "Animal Herd",
            "Broiler Batch",
            "Budget Forecasting",
            "Contract Farming Agreement",
            "Crop Cycle",
            "Dairy Cow Herd",
            "Fish Batch",
            "Goat Herd",
            "Greenhouse Cycle",
            "Pig Batch",
            "Poultry Flock",
            "Standard Cost Calculation BOM",
        }
        present = {
            json.loads(path.read_text(encoding="utf-8")).get("name")
            for path in APP_ROOT.glob("**/doctype/**/*.json")
        }
        self.assertFalse(removed & present)
        install = (APP_ROOT / "install.py").read_text(encoding="utf-8")
        fish_cleanup = install.split("def retire_removed_fish_masters():", 1)[1].split(
            "\ndef ", 1
        )[0]
        self.assertIn('"Farm Type Managed Item"', fish_cleanup)
        self.assertIn('"Farm Type Multiselect"', fish_cleanup)

    def test_ias41_reconciliation_report_is_installed(self):
        report = APP_ROOT / "biological_assets" / "report" / "biological_asset_gl_reconciliation"
        self.assertTrue((report / "biological_asset_gl_reconciliation.json").is_file())
        valuation = (APP_ROOT / "biological_assets" / "valuation.py").read_text(encoding="utf-8")
        self.assertIn("get_biological_asset_gl_reconciliation", valuation)
        self.assertIn('"GL Entry"', valuation)
        self.assertIn("Reclassification Required", valuation)
        get_company_body = valuation.split("def get_company(asset):", 1)[1].split(
            "\ndef ", 1
        )[0]
        self.assertLess(
            get_company_body.index('"Farm", asset.farm, "owner_name"'),
            get_company_body.index('"Farm Management Settings"'),
        )
        self.assertIn(
            "setup_biological_asset_accounts(get_company(asset))", valuation
        )

    def test_v15_bench_gate_script_covers_clean_and_upgrade_modes(self):
        script = (REPO_ROOT / "scripts" / "test_erpnext_v15.sh").read_text(encoding="utf-8")
        self.assertIn('MODE="${MODE:-clean}"', script)
        self.assertIn('MODE" == "upgrade', script)
        self.assertGreaterEqual(script.count('migrate'), 4)
        self.assertIn("run-tests --module farm_management.tests.test_repository_contracts", script)
        self.assertIn("run-tests --app farm_management --skip-test-records", script)


if __name__ == "__main__":
    unittest.main()
