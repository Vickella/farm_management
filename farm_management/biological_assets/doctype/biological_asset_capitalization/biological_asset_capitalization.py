import frappe
from frappe.model.document import Document
from frappe.utils import flt
from farm_management.server_validation import validate_asset_context, validate_date_order

from farm_management.biological_assets.valuation import apply_capitalization, reverse_capitalization


class BiologicalAssetCapitalization(Document):
    def validate(self):
        asset = validate_asset_context(self.biological_asset, active=True)
        if not flt(self.amount) and not flt(self.quantity_delta):
            frappe.throw("Enter a capitalized amount or quantity movement.")
        if flt(self.amount) < 0:
            frappe.throw("Capitalized amount cannot be negative.")
        if flt(self.quantity_delta) < 0:
            frappe.throw("Capitalization Quantity Delta cannot be negative.")
        validate_date_order(asset.acquisition_date, self.posting_date, "Asset Acquisition Date", "Posting Date")
        if self.project and asset.linked_project and self.project != asset.linked_project:
            frappe.throw("Capitalization Project must match the Biological Asset Project.")
        self.project = self.project or asset.linked_project
        if self.source_doctype and self.source_name:
            duplicate = frappe.db.exists(
                "Biological Asset Capitalization",
                {
                    "source_doctype": self.source_doctype,
                    "source_name": self.source_name,
                    "docstatus": ["<", 2],
                    "name": ["!=", self.name or ""],
                },
            )
            if duplicate:
                frappe.throw(f"Source {self.source_doctype} {self.source_name} is already capitalized.")

    def on_submit(self):
        apply_capitalization(self)

    def on_cancel(self):
        reverse_capitalization(self)

@frappe.whitelist()
def calculate_amount(docname, asset):
    frappe.has_permission(
        "Biological Asset Capitalization", ptype="write", throw=True
    )
    frappe.get_doc("Biological Asset", asset).check_permission("read")
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
