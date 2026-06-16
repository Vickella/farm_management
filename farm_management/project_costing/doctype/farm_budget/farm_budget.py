import frappe
from frappe.model.document import Document
from frappe.utils import flt

class FarmBudget(Document):
    def validate(self):
        self.calculate_variance()

    def calculate_variance(self):
        total_budget = 0
        total_actual = 0
        for item in self.budget_items:
            item.budgeted_amount = flt(item.budgeted_quantity) * flt(item.budgeted_unit_cost)
            item.variance = flt(item.actual_amount) - flt(item.budgeted_amount)
            if flt(item.budgeted_amount) != 0:
                item.variance_percent = flt((item.variance / item.budgeted_amount) * 100, 2)
            item.variance_type = "Adverse" if flt(item.variance) > 0 else "Favourable"
            total_budget += flt(item.budgeted_amount)
            total_actual += flt(item.actual_amount)
        self.total_budget = total_budget
        self.total_actual = total_actual
        self.total_variance = total_actual - total_budget
