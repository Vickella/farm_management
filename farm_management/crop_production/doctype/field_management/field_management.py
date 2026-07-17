import frappe
from frappe.model.document import Document
from frappe.utils import flt
from farm_management.server_validation import apply_project_context, validate_unique_rows


class FieldManagement(Document):
    def validate(self):
        project = apply_project_context(self)
        if project.managed_item_doctype != "Crop Type":
            frappe.throw("Field Management can only use a crop Agriculture Project.")
        if not self.get("requirements"):
            frappe.throw("Add at least one Item to the Requirements table.")
        self.total_estimated_cost = 0
        validate_unique_rows(self.requirements, ("item",), "Requirement Item")
        for row in self.get("requirements", []):
            if flt(row.quantity) <= 0:
                frappe.throw(f"Requirement quantity must be greater than zero on row {row.idx}.")
            item = frappe.db.get_value(
                "Item", row.item, ["stock_uom", "valuation_rate"], as_dict=True
            )
            if not item:
                frappe.throw(f"Select a valid Item on requirement row {row.idx}.")
            row.uom = item.stock_uom
            if not flt(row.valuation_rate):
                row.valuation_rate = flt(item.valuation_rate)
            row.estimated_amount = flt(row.quantity) * flt(row.valuation_rate)
            self.total_estimated_cost += row.estimated_amount
