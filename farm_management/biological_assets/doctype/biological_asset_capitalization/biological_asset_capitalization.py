import frappe
from frappe.model.document import Document
from frappe.utils import flt

from farm_management.biological_assets.valuation import apply_capitalization, reverse_capitalization


class BiologicalAssetCapitalization(Document):
    def validate(self):
        if not flt(self.amount) and not flt(self.quantity_delta):
            frappe.throw("Enter a capitalized amount or quantity movement.")
        if flt(self.amount) < 0:
            frappe.throw("Capitalized amount cannot be negative.")

    def on_submit(self):
        apply_capitalization(self)

    def on_cancel(self):
        reverse_capitalization(self)

@frappe.whitelist()
def calculate_amount(docname, asset):
    health_events = frappe.get_all(
        "Livestock Health Event",
        filters={
            "biological_asset": asset,
            "docstatus": 1,
            "capitalize_cost": 1,
            "capitalized_to_asset": 0,
        },
        fields=["name", "cost"],
    )
    return sum(flt(event.cost) for event in health_events)
