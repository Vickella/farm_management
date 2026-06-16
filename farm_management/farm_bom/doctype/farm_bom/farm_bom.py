import frappe
from frappe.model.document import Document
from frappe.utils import flt

class FarmBOM(Document):
    def validate(self):
        self.calculate_totals()

    def calculate_totals(self):
        total = 0
        for item in self.bom_items:
            item.total_cost = flt(item.quantity) * flt(item.unit_cost)
            total += flt(item.total_cost)
        self.total_estimated_cost = total
