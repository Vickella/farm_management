import frappe
from frappe.model.document import Document
from frappe.utils import flt

from farm_management.biological_assets.valuation import create_fair_value_journal_entry


class BiologicalAssetValuation(Document):
    def validate(self):
        asset = frappe.get_doc("Biological Asset", self.biological_asset)
        self.previous_net_fair_value = flt(asset.net_fair_value)
        self.previous_current_fair_value = flt(asset.current_fair_value)
        self.previous_cost_to_sell = flt(asset.cost_to_sell)
        self.net_fair_value = flt(self.current_fair_value) - flt(self.cost_to_sell)
        self.fair_value_movement = flt(self.net_fair_value) - flt(self.previous_net_fair_value)

    def on_submit(self):
        asset = frappe.get_doc("Biological Asset", self.biological_asset)
        asset.valuation_method = self.valuation_method
        asset.current_fair_value = self.current_fair_value
        asset.cost_to_sell = self.cost_to_sell
        asset.last_valuation_date = self.valuation_date
        asset.recalculate_valuation()
        asset.save(ignore_permissions=True)

        if self.post_journal_entry:
            create_fair_value_journal_entry(asset)
            self.db_set("journal_entry", asset.last_journal_entry, update_modified=False)

    def on_cancel(self):
        if self.journal_entry and frappe.db.exists("Journal Entry", self.journal_entry):
            journal_entry = frappe.get_doc("Journal Entry", self.journal_entry)
            if journal_entry.docstatus == 1:
                journal_entry.cancel()

        asset = frappe.get_doc("Biological Asset", self.biological_asset)
        asset.current_fair_value = self.previous_current_fair_value
        asset.cost_to_sell = self.previous_cost_to_sell
        asset.recalculate_valuation()
        asset.save(ignore_permissions=True)
