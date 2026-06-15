from frappe.model.document import Document
from frappe.utils import flt


class FarmBOMItem(Document):
    def validate(self):
        self.total_cost = flt(self.quantity) * flt(self.unit_cost)
