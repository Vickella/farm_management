import frappe
from frappe.model.document import Document
from frappe.utils import flt


class FarmCashbook(Document):
    def validate(self):
        if flt(self.amount) <= 0:
            frappe.throw("Amount must be greater than zero.")
        if self.project and not frappe.db.exists("Project", self.project):
            frappe.throw("Select a valid Project or leave Project blank.")

    def on_submit(self):
        self.create_journal_entry()

    def create_journal_entry(self):
        company = self.get_company()
        expense_account = frappe.db.get_value("Company", company, "default_expense_account")
        if not expense_account:
            frappe.throw("Please set a Default Expense Account in Company to auto-post Journal Entries.")

        cost_center = frappe.db.get_value("Company", company, "cost_center")
        remark_parts = [self.project_type, self.expense_type, self.description]
        remark = " | ".join(part for part in remark_parts if part)

        je = frappe.new_doc("Journal Entry")
        je.posting_date = self.date
        je.voucher_type = "Journal Entry"
        je.company = company
        je.user_remark = remark or "Farm Cashbook expense"

        debit_row = {
            "account": expense_account,
            "debit_in_account_currency": flt(self.amount),
            "credit_in_account_currency": 0.0,
            "cost_center": cost_center,
        }
        credit_row = {
            "account": self.payment_account,
            "debit_in_account_currency": 0.0,
            "credit_in_account_currency": flt(self.amount),
            "cost_center": cost_center,
        }
        if self.project:
            debit_row["project"] = self.project
            credit_row["project"] = self.project

        je.append("accounts", debit_row)
        je.append("accounts", credit_row)
        je.insert(ignore_permissions=True)
        je.submit()

        frappe.msgprint(f"Journal Entry {je.name} created successfully.")
        self.db_set("journal_entry", je.name)

    def get_company(self):
        if self.farm:
            company = frappe.db.get_value("Farm", self.farm, "owner_name")
            if company:
                return company
        settings_company = frappe.db.get_single_value("Farm Management Settings", "default_company")
        return settings_company or frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")