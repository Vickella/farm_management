from frappe.model.document import Document
from frappe.utils import flt


class FarmBudgetItem(Document):
    def validate(self):
        self.budgeted_amount = flt(self.budgeted_quantity) * flt(
            self.budgeted_unit_cost
        )
