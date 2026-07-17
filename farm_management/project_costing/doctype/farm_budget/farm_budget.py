import frappe
from frappe.model.document import Document
from frappe.utils import flt
from farm_management.server_validation import apply_project_context, get_farm_context, validate_date_order, validate_unique_rows

class FarmBudget(Document):
    def validate(self):
        self.set_context_and_bom_items()
        self.validate_dates()
        self.validate_items()
        self.calculate_budget()

    def validate_dates(self):
        validate_date_order(self.budget_period_start, self.budget_period_end, "Budget Period Start", "Budget Period End")

    def set_context_and_bom_items(self):
        project = apply_project_context(self)
        if not self.budget_title:
            self.budget_title = f"{self.project} Budget"
        self.farm = project.farm
        self.budget_period_start = (
            self.budget_period_start or project.expected_start_date
        )
        self.budget_period_end = self.budget_period_end or project.expected_end_date
        farm = get_farm_context(self.farm)
        if project.company and project.company != farm.owner_name:
            frappe.throw("Budget Project and Farm must belong to the same Company.")
        if not self.farm_bom:
            return
        bom = frappe.get_doc("Farm BOM", self.farm_bom)
        if bom.project != self.project or bom.farm != self.farm:
            frappe.throw("Farm BOM, Project, and Farm must describe the same operation.")
        if not self.budget_items:
            for source in bom.bom_items:
                self.append("budget_items", {
                    "item_category": source.item_category,
                    "item": source.item,
                    "item_description": source.item_description,
                    "budgeted_quantity": source.quantity,
                    "unit": source.unit,
                    "budgeted_unit_cost": source.unit_cost,
                })

    def calculate_budget(self):
        total_budget = 0
        validate_unique_rows(self.budget_items, ("item", "expense_account", "item_description"), "Budget Item")
        company = get_farm_context(self.farm).owner_name
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
            if flt(item.budgeted_quantity) < 0 or flt(item.budgeted_unit_cost) < 0:
                frappe.throw(f"Budget quantity and rate cannot be negative on row {item.idx}.")
            if item.item:
                master = frappe.db.get_value("Item", item.item, ["stock_uom", "disabled"], as_dict=True)
                if not master or master.disabled:
                    frappe.throw(f"Select an enabled Item on budget row {item.idx}.")
                item.unit = master.stock_uom
            if item.expense_account:
                account = frappe.db.get_value("Account", item.expense_account, ["company", "is_group"], as_dict=True)
                if not account or account.is_group or account.company != company:
                    frappe.throw(f"Expense Account on row {item.idx} must be a ledger account for {company}.")
