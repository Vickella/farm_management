import frappe
from frappe.model.document import Document
from frappe.utils import getdate

class FarmCashbook(Document):
	def on_submit(self):
		self.create_journal_entry()
		
	def create_journal_entry(self):
		# Default expense account logic (can be refined via settings in the future)
		# Assuming we are looking for a standard expense account if not specified.
		# For this demo, we use a placeholder or require user to have setup.
		# Actually, since payment_account is specified, we need the debit account.
		# Let's assume the user has a default Farm Expense Account in settings or we fetch by name.
		expense_account = frappe.db.get_value("Company", frappe.defaults.get_user_default("Company"), "default_expense_account")
		if not expense_account:
			frappe.throw("Please set a Default Expense Account in Company to auto-post Journal Entries.")
			
		je = frappe.new_doc("Journal Entry")
		je.posting_date = self.date
		je.voucher_type = "Journal Entry"
		je.company = frappe.defaults.get_user_default("Company")
		je.user_remark = f"{self.project_type} Expense: {self.description} ({self.expense_type})"
		
		# Debit the expense account
		je.append("accounts", {
			"account": expense_account,
			"debit_in_account_currency": self.amount,
			"credit_in_account_currency": 0.0,
			"project": self.project_type, # Using project_type as a rough proxy if Project isn't linked
			"cost_center": frappe.db.get_value("Company", je.company, "cost_center")
		})
		
		# Credit the payment account (Bank/Cash)
		je.append("accounts", {
			"account": self.payment_account,
			"debit_in_account_currency": 0.0,
			"credit_in_account_currency": self.amount,
			"project": self.project_type,
			"cost_center": frappe.db.get_value("Company", je.company, "cost_center")
		})
		
		je.insert(ignore_permissions=True)
		je.submit()
		
		frappe.msgprint(f"Journal Entry {je.name} created successfully.")
		self.db_set("journal_entry", je.name)
