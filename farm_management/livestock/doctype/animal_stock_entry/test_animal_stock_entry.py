import unittest
import json
from pathlib import Path

from farm_management.livestock.doctype.animal_stock_entry.animal_stock_entry import get_empty_asset_status


class TestAnimalStockEntry(unittest.TestCase):
    def test_sale_fields_are_declared(self):
        path = Path(__file__).with_name("animal_stock_entry.json")
        doc = json.loads(path.read_text(encoding="utf-8"))
        fieldnames = {field["fieldname"] for field in doc["fields"]}
        self.assertIn("sale_amount", fieldnames)
        self.assertIn("journal_entry", fieldnames)

    def test_empty_asset_status_by_entry_type(self):
        self.assertEqual(get_empty_asset_status("Sale"), "Sold")
        self.assertEqual(get_empty_asset_status("Death"), "Dead Loss")
        self.assertEqual(get_empty_asset_status("Issue"), "Harvested")
