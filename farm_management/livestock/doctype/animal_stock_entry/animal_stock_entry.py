import frappe
from frappe.model.document import Document
from frappe.utils import flt, today

from farm_management.biological_assets.valuation import (
    create_capitalization_document,
    reduce_asset_quantity,
    restore_asset_quantity,
)


class AnimalStockEntry(Document):
    def validate(self):
        if not self.posting_date:
            self.posting_date = today()
        if flt(self.quantity) <= 0:
            frappe.throw("Quantity must be greater than zero.")
        self.amount = flt(self.quantity) * flt(self.rate) if not flt(self.amount) else flt(self.amount)

    def on_submit(self):
        if self.entry_type in ("Receipt", "Purchase", "Birth", "Transfer In", "Opening", "Adjustment Increase"):
            self.apply_increase()
        elif self.entry_type in ("Issue", "Sale", "Death", "Transfer Out", "Adjustment Decrease"):
            self.apply_decrease()
        elif self.entry_type == "Cost Capitalization":
            self.apply_cost_capitalization()

    def on_cancel(self):
        if self.capitalization and frappe.db.exists("Biological Asset Capitalization", self.capitalization):
            cap = frappe.get_doc("Biological Asset Capitalization", self.capitalization)
            if cap.docstatus == 1:
                cap.cancel()
        if self.asset_value_reduction:
            restore_asset_quantity(
                self.biological_asset,
                self.quantity,
                self.asset_value_reduction,
                self.doctype,
                self.name,
            )

    def apply_increase(self):
        capitalization = create_capitalization_document(
            biological_asset=self.biological_asset,
            amount=self.amount,
            capitalization_type=get_capitalization_type(self.entry_type),
            source_doctype=self.doctype,
            source_name=self.name,
            remarks=f"Animal stock {self.entry_type}",
            quantity_delta=self.quantity,
            project=self.project,
        )
        if capitalization:
            self.db_set("capitalization", capitalization, update_modified=False)


def get_capitalization_type(entry_type):
    if entry_type == "Birth":
        return "Birth"
    if entry_type == "Cost Capitalization":
        return "Other"
    return "Purchase"

    def apply_decrease(self):
        value_reduction = reduce_asset_quantity(
            self.biological_asset,
            self.quantity,
            self.doctype,
            self.name,
        )
        self.db_set("asset_value_reduction", value_reduction, update_modified=False)

    def apply_cost_capitalization(self):
        capitalization = create_capitalization_document(
            biological_asset=self.biological_asset,
            amount=self.amount,
            capitalization_type="Other",
            source_doctype=self.doctype,
            source_name=self.name,
            remarks=f"Animal stock cost capitalization: {self.item or ''}",
            quantity_delta=0,
            project=self.project,
        )
        if capitalization:
            self.db_set("capitalization", capitalization, update_modified=False)
