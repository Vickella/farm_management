from frappe.model.document import Document
from frappe.utils import flt


class FarmBudget(Document):
    def validate(self):
        self.total_budget = 0
        self.total_actual = 0
        for item in self.get("budget_items"):
            item.budgeted_amount = flt(item.budgeted_quantity) * flt(
                item.budgeted_unit_cost
            )
            item.variance = flt(item.actual_amount) - flt(item.budgeted_amount)
            item.variance_percent = (
                item.variance / item.budgeted_amount * 100
                if item.budgeted_amount
                else 0
            )
            item.variance_type = "Adverse" if item.variance > 0 else "Favourable"
            self.total_budget += item.budgeted_amount
            self.total_actual += flt(item.actual_amount)
        self.total_variance = self.total_actual - self.total_budget
