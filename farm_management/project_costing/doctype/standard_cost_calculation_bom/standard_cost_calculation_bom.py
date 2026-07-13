from frappe.model.document import Document
from frappe.utils import flt

import frappe

class StandardCostCalculationBOM(Document):
    def validate(self):
        if flt(self.target_quantity) <= 0:
            frappe.throw("Target Quantity must be greater than zero.")
        if not self.standard_costs:
            frappe.throw("Add at least one standard cost row.")

        total = 0
        for row in self.standard_costs:
            if flt(row.quantity) <= 0:
                frappe.throw(f"Quantity must be greater than zero on row {row.idx}.")
            stock_uom = frappe.db.get_value("Item", row.item, "stock_uom")
            if stock_uom and row.unit != stock_uom:
                frappe.throw(
                    f"Unit on row {row.idx} must match Item {row.item} stock UOM ({stock_uom})."
                )
            row.amount = flt(row.quantity) * flt(row.rate)
            total += flt(row.amount)

        self.total_standard_cost = total
        self.standard_cost_per_unit = total / flt(self.target_quantity)
