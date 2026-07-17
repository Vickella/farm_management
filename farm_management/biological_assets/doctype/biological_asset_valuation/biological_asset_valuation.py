import frappe
from frappe.model.document import Document
from frappe.utils import flt
from farm_management.server_validation import validate_asset_context, validate_date_order

from farm_management.biological_assets.valuation import create_fair_value_journal_entry


class BiologicalAssetValuation(Document):
    def validate(self):
        asset = frappe.get_doc("Biological Asset", self.biological_asset)
        validate_asset_context(asset.name, active=True)
        validate_date_order(asset.acquisition_date, self.valuation_date, "Asset Acquisition Date", "Valuation Date")
        if flt(self.current_fair_value) < 0 or flt(self.cost_to_sell) < 0:
            frappe.throw("Current Fair Value and Cost to Sell cannot be negative.")
        if flt(self.cost_to_sell) > flt(self.current_fair_value):
            frappe.throw("Cost to Sell cannot exceed Current Fair Value.")
        duplicate = frappe.db.exists(
            "Biological Asset Valuation",
            {
                "biological_asset": self.biological_asset,
                "valuation_date": self.valuation_date,
                "docstatus": ["<", 2],
                "name": ["!=", self.name or ""],
            },
        )
        if duplicate:
            frappe.throw("Only one active valuation per Biological Asset and date is allowed.")
        self.previous_net_fair_value = flt(asset.net_fair_value)
        self.previous_current_fair_value = flt(asset.current_fair_value)
        self.previous_cost_to_sell = flt(asset.cost_to_sell)
        self.valuation_snapshot = frappe.as_json(
            {
                fieldname: asset.get(fieldname)
                for fieldname in (
                    "valuation_method",
                    "current_fair_value",
                    "cost_to_sell",
                    "net_fair_value",
                    "accumulated_gain_loss",
                    "last_posted_net_fair_value",
                    "last_valuation_date",
                    "last_journal_entry",
                )
            }
        )
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
            create_fair_value_journal_entry(
                asset,
                delta=self.fair_value_movement,
                posting_date=self.valuation_date,
            )
            self.db_set("journal_entry", asset.last_journal_entry, update_modified=False)

    def on_cancel(self):
        newer = frappe.db.exists(
            "Biological Asset Valuation",
            {
                "biological_asset": self.biological_asset,
                "docstatus": 1,
                "creation": [">", self.creation],
            },
        )
        if newer:
            frappe.throw("Cancel later Biological Asset Valuations before cancelling this valuation.")
        if self.journal_entry and frappe.db.exists("Journal Entry", self.journal_entry):
            journal_entry = frappe.get_doc("Journal Entry", self.journal_entry)
            if journal_entry.docstatus == 1:
                journal_entry.cancel()

        asset = frappe.get_doc("Biological Asset", self.biological_asset)
        snapshot = frappe.parse_json(self.valuation_snapshot or "{}")
        for fieldname, value in snapshot.items():
            asset.set(fieldname, value)
        asset.flags.ignore_validate = True
        asset.save(ignore_permissions=True)
        if "last_valuation_date" in snapshot:
            asset.db_set(
                "last_valuation_date",
                snapshot["last_valuation_date"],
                update_modified=False,
            )
