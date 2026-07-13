import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt

import frappe

class BudgetForecasting(Document):
    def validate(self):
        if cint(self.year) < 2000 or cint(self.year) > 2100:
            frappe.throw("Year must be between 2000 and 2100.")
        bom_project = frappe.db.get_value("Farm BOM", self.farm_bom, "project")
        if bom_project and bom_project != self.project:
            frappe.throw("Budget Forecasting Project must match the Farm BOM Project.")
        if not self.expected_expenses:
            frappe.throw("Add at least one expected expense.")

        seen = set()
        total = 0
        for row in self.expected_expenses:
            key = (row.expense_account, row.month)
            if key in seen:
                frappe.throw(
                    f"Expense Account and Month are duplicated on row {row.idx}."
                )
            seen.add(key)
            if flt(row.amount) < 0:
                frappe.throw(f"Amount cannot be negative on row {row.idx}.")
            total += flt(row.amount)
        self.total_forecast = total
