import frappe
from frappe.model.document import Document
from frappe.utils import flt

class FarmBudget(Document):
    def validate(self):
        self.validate_dates()
        self.validate_items()
        self.calculate_budget()

    def validate_dates(self):
        if self.budget_period_end and self.budget_period_start and self.budget_period_end < self.budget_period_start:
            frappe.throw("Budget Period End cannot be before Budget Period Start.")

    def calculate_budget(self):
        total_budget = 0
        for item in self.budget_items:
            item.budgeted_amount = flt(item.budgeted_quantity) * flt(item.budgeted_unit_cost)
            total_budget += flt(item.budgeted_amount)
        self.total_budget = total_budget

    def validate_items(self):
        if not self.budget_items:
            frappe.throw("Add at least one budget item.")
        for item in self.budget_items:
            if not item.item and not item.expense_account:
                frappe.throw(
                    f"Select an Item or Expense Account on budget row {item.idx} "
                    "so actual costs can be calculated."
                )
