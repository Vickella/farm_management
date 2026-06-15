from frappe.model.document import Document
from frappe.utils import flt


class FarmBOM(Document):
    def validate(self):
        total = 0
        for item in self.get("bom_items"):
            item.total_cost = flt(item.quantity) * flt(item.unit_cost)
            total += item.total_cost
        self.total_estimated_cost = total
