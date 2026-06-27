import frappe
from frappe.model.document import Document
from frappe.utils import flt


class FarmCashbook(Document):
    def validate(self):
        if flt(self.amount) <= 0:
            frappe.throw("Amount must be greater than zero.")
        if not self.debit_account:
            frappe.throw("Select the account to debit.")
        if not self.credit_account:
            frappe.throw("Select the account to credit.")
        if self.debit_account == self.credit_account:
            frappe.throw("Debit Account and Credit Account cannot be the same.")
        self.validate_account(self.debit_account, "Debit Account")
        self.validate_account(self.credit_account, "Credit Account")
        if self.project and not frappe.db.exists("Project", self.project):
            frappe.throw("Select a valid Project or leave Project blank.")

    def on_submit(self):
        self.create_journal_entry()

    def create_journal_entry(self):
        company = self.get_company()
        if not company:
            frappe.throw("Set a Company on Farm Management Settings or as your user default before posting.")

        cost_center = frappe.db.get_value("Company", company, "cost_center")
        remark_parts = [self.project_type, self.expense_type, self.description]
        remark = " | ".join(part for part in remark_parts if part) or "Farm Cashbook transaction"

        je = frappe.new_doc("Journal Entry")
        je.posting_date = self.date
        je.voucher_type = "Journal Entry"
        je.company = company
        je.user_remark = remark

        debit_row = {
            "account": self.debit_account,
            "debit_in_account_currency": flt(self.amount),
            "credit_in_account_currency": 0.0,
            "cost_center": cost_center,
        }
        credit_row = {
            "account": self.credit_account,
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

    def validate_account(self, account, label):
        account_doc = frappe.db.get_value(
            "Account",
            account,
            ["name", "is_group", "company"],
            as_dict=True,
        )
        if not account_doc:
            frappe.throw(f"Select a valid {label}.")
        if account_doc.is_group:
            frappe.throw(f"{label} must be a ledger account, not a group account.")
        company = self.get_company()
        if company and account_doc.company != company:
            frappe.throw(f"{label} must belong to company {company}.")

    def get_company(self):
        if self.farm:
            company = frappe.db.get_value("Farm", self.farm, "owner_name")
            if company:
                return company
        settings_company = frappe.db.get_single_value("Farm Management Settings", "default_company")
        return settings_company or frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")