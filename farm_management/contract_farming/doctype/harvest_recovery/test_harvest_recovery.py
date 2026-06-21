import unittest
import json
from pathlib import Path


class TestHarvestRecovery(unittest.TestCase):
    def test_journal_entry_field_declared(self):
        path = Path(__file__).with_name("harvest_recovery.json")
        doc = json.loads(path.read_text(encoding="utf-8"))
        fieldnames = {field["fieldname"] for field in doc["fields"]}
        self.assertIn("journal_entry", fieldnames)
