import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPO_ROOT / "farm_management"


def get_doctype(name):
    for path in APP_ROOT.glob("**/doctype/**/*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("name") == name:
            return data
    raise AssertionError(f"DocType not found: {name}")


class TestRepositoryContracts(unittest.TestCase):
    def test_all_doctype_json_and_field_order_are_valid(self):
        for path in APP_ROOT.glob("**/doctype/**/*.json"):
            with self.subTest(path=path):
                data = json.loads(path.read_text(encoding="utf-8"))
                fieldnames = [row.get("fieldname") for row in data.get("fields", [])]
                self.assertEqual(len(fieldnames), len(set(fieldnames)))
                self.assertEqual(set(data.get("field_order", [])), set(fieldnames))

    def test_erpnext_is_a_required_app(self):
        hooks = (APP_ROOT / "hooks.py").read_text(encoding="utf-8")
        self.assertIn('required_apps = ["erpnext"]', hooks)

    def test_transactional_bom_fixture_is_excluded(self):
        install = (APP_ROOT / "install.py").read_text(encoding="utf-8")
        self.assertIn('EXCLUDED_INSTALL_FIXTURES = {"farm_bom.json"}', install)

    def test_master_selection_fields_are_links(self):
        expected = {
            ("Crop Cycle", "crop_variety"): ("Link", "Crop Type"),
            ("Greenhouse Cycle", "crop"): ("Link", "Crop Type"),
            ("Cattle Herd", "breed"): ("Link", "Livestock Breed"),
            ("Fish Batch", "species"): ("Link", "Livestock Species"),
            ("Farm Pen", "managed_species"): ("Link", "Livestock Species"),
            ("Farm Pond", "managed_species"): ("Link", "Livestock Species"),
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

    def test_operational_units_use_uom_master(self):
        for doctype, fieldname in (
            ("Biological Asset", "unit"),
            ("Harvest Transaction", "unit"),
            ("Contract Farming Agreement", "unit"),
            ("Farm BOM", "planned_quantity_unit"),
            ("Crop Type", "yield_unit"),
            ("Animal Stock Entry", "unit"),
            ("Standard Cost Calculation BOM", "unit"),
        ):
            with self.subTest(doctype=doctype, fieldname=fieldname):
                field = next(
                    row
                    for row in get_doctype(doctype)["fields"]
                    if row.get("fieldname") == fieldname
                )
                self.assertEqual(field.get("fieldtype"), "Link")
                self.assertEqual(field.get("options"), "UOM")

    def test_weather_source_contains_no_fallback_api_key(self):
        weather = (
            APP_ROOT / "farm_management" / "api" / "weather.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("DEFAULT_OPENWEATHER_API_KEY", weather)

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
        controller = (
            APP_ROOT / "crop_production" / "doctype" / "harvest_log" / "harvest_log.py"
        ).read_text(encoding="utf-8")
        self.assertIn('"doctype": "Harvest Transaction"', controller)
        self.assertIn("transaction.submit()", controller)
        transaction = get_doctype("Harvest Transaction")
        unit = next(field for field in transaction["fields"] if field["fieldname"] == "unit")
        self.assertNotIn("fetch_from", unit)

    def test_cancelable_doctypes_are_amendable_and_statuses_are_synchronized(self):
        for doctype in ("Biological Asset Valuation", "Biological Asset Capitalization"):
            fields = {field["fieldname"] for field in get_doctype(doctype)["fields"]}
            self.assertIn("amended_from", fields)
        hooks = (APP_ROOT / "hooks.py").read_text(encoding="utf-8")
        self.assertIn("sync_status_on_submit", hooks)
        install = (APP_ROOT / "install.py").read_text(encoding="utf-8")
        self.assertIn("ensure_amendable_doctypes", install)

    def test_workspace_contains_core_farm_accounting_reports(self):
        install = (APP_ROOT / "install.py").read_text(encoding="utf-8")
        self.assertIn('"Profit and Loss Statement", "Report"', install)
        self.assertIn('"Accounts Receivable Summary", "Report"', install)
        self.assertIn('"Accounts Payable Summary", "Report"', install)
        self.assertNotIn('("Poultry Infrastructure", "DocType")', install)

    def test_live_animal_sales_and_purchases_require_standard_invoices(self):
        doc = get_doctype("Animal Stock Entry")
        fields = {row["fieldname"]: row for row in doc["fields"]}
        self.assertEqual(fields["purchase_invoice"].get("options"), "Purchase Invoice")
        self.assertEqual(fields["sales_invoice"].get("options"), "Sales Invoice")
        controller = (
            APP_ROOT / "livestock" / "doctype" / "animal_stock_entry" / "animal_stock_entry.py"
        ).read_text(encoding="utf-8")
        self.assertIn('invoice.docstatus != 1', controller)
        self.assertIn('invoice.get("is_return")', controller)
        self.assertIn("base_net_amount", controller)

    def test_contract_accounting_implements_both_directions(self):
        accounting = (APP_ROOT / "contract_farming" / "accounting.py").read_text(encoding="utf-8")
        self.assertIn('Receiving Contract (Liability)', accounting)
        self.assertIn("create_received_input_journal", accounting)
        self.assertIn("create_receiving_harvest_journal", accounting)
        self.assertIn('get_party_account("Customer"', accounting)

    def test_ias41_reconciliation_report_is_installed(self):
        report = APP_ROOT / "biological_assets" / "report" / "biological_asset_gl_reconciliation"
        self.assertTrue((report / "biological_asset_gl_reconciliation.json").is_file())
        valuation = (APP_ROOT / "biological_assets" / "valuation.py").read_text(encoding="utf-8")
        self.assertIn("get_biological_asset_gl_reconciliation", valuation)
        self.assertIn('"GL Entry"', valuation)

    def test_v15_bench_gate_script_covers_clean_and_upgrade_modes(self):
        script = (REPO_ROOT / "scripts" / "test_erpnext_v15.sh").read_text(encoding="utf-8")
        self.assertIn('MODE="${MODE:-clean}"', script)
        self.assertIn('MODE" == "upgrade', script)
        self.assertGreaterEqual(script.count('migrate'), 4)
        self.assertIn("run-tests --module farm_management.tests.test_repository_contracts", script)
        self.assertIn("run-tests --app farm_management --skip-test-records", script)


if __name__ == "__main__":
    unittest.main()
