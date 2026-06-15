from frappe.model.document import Document
from frappe.utils import flt


class FarmBudgetItem(Document):
    def validate(self):
        self.budgeted_amount = flt(self.budgeted_quantity) * flt(
            self.budgeted_unit_cost
        )
        self.variance = flt(self.actual_amount) - flt(self.budgeted_amount)
        self.variance_percent = (
            self.variance / self.budgeted_amount * 100 if self.budgeted_amount else 0
        )
        self.variance_type = "Adverse" if self.variance > 0 else "Favourable"
