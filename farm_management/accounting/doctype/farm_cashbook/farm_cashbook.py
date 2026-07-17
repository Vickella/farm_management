import frappe
from frappe.model.document import Document
from frappe.utils import flt
from farm_management.server_validation import apply_project_context, get_farm_context, validate_unique_rows


class FarmCashbook(Document):
    def validate(self):
        farm = get_farm_context(self.farm)
        if self.project:
            project = apply_project_context(self)
            if project.company and project.company != farm.owner_name:
                frappe.throw("Cashbook Project and Farm must belong to the same Company.")
        if not self.get("entries"):
            frappe.throw("Add at least one transaction row.")

        self.total_amount = 0
        validate_unique_rows(
            self.get("entries"),
            ("debit_account", "credit_account", "project", "cost_center", "amount", "expense_type", "description"),
            "Cashbook transaction",
        )
        for row in self.get("entries"):
            self.validate_entry(row)
            self.total_amount += flt(row.amount)

    def on_submit(self):
        self.create_journal_entry()

    def on_cancel(self):
        if not self.journal_entry or not frappe.db.exists("Journal Entry", self.journal_entry):
            return
        journal_entry = frappe.get_doc("Journal Entry", self.journal_entry)
        if journal_entry.docstatus == 1:
            journal_entry.flags.ignore_permissions = True
            journal_entry.cancel()

    def validate_entry(self, row):
        if flt(row.amount) <= 0:
            frappe.throw(f"Amount must be greater than zero on row {row.idx}.")
        if not row.debit_account:
            frappe.throw(f"Select the account to debit on row {row.idx}.")
        if not row.credit_account:
            frappe.throw(f"Select the account to credit on row {row.idx}.")
        if row.debit_account == row.credit_account:
            frappe.throw(f"Debit Account and Credit Account cannot be the same on row {row.idx}.")
        self.validate_account(row.debit_account, f"Debit Account on row {row.idx}")
        self.validate_account(row.credit_account, f"Credit Account on row {row.idx}")
        if row.project and not frappe.db.exists("Project", row.project):
            frappe.throw(f"Select a valid Project on row {row.idx} or leave it blank.")
        if row.cost_center:
            self.validate_cost_center(row.cost_center, row.idx)

    def create_journal_entry(self):
        if self.journal_entry and frappe.db.exists("Journal Entry", self.journal_entry):
            journal_entry = frappe.get_doc("Journal Entry", self.journal_entry)
            if journal_entry.docstatus == 1:
                return
        company = self.get_company()
        if not company:
            frappe.throw("Set a Company on Farm Management Settings or as your user default before posting.")

        default_cost_center = frappe.db.get_value("Company", company, "cost_center")
        remark = self.get_journal_remark()

        je = frappe.new_doc("Journal Entry")
        je.posting_date = self.date
        je.voucher_type = "Journal Entry"
        je.company = company
        je.user_remark = remark

        for row in self.get("entries"):
            project = row.project or self.project
            cost_center = row.cost_center or default_cost_center
            self.append_journal_row(
                je,
                account=row.debit_account,
                debit=flt(row.amount),
                credit=0,
                project=project,
                cost_center=cost_center,
                user_remark=row.description or row.expense_type,
            )
            self.append_journal_row(
                je,
                account=row.credit_account,
                debit=0,
                credit=flt(row.amount),
                project=project,
                cost_center=cost_center,
                user_remark=row.description or row.expense_type,
            )

        je.insert(ignore_permissions=True)
        je.submit()

        frappe.msgprint(f"Journal Entry {je.name} created successfully.")
        self.db_set("journal_entry", je.name)

    def append_journal_row(self, journal_entry, account, debit=0, credit=0, project=None, cost_center=None, user_remark=None):
        row = {
            "account": account,
            "debit_in_account_currency": flt(debit),
            "credit_in_account_currency": flt(credit),
        }
        if cost_center:
            row["cost_center"] = cost_center
        if project:
            row["project"] = project
        if user_remark:
            row["user_remark"] = user_remark
        journal_entry.append("accounts", row)

    def get_journal_remark(self):
        parts = [self.description]
        row_labels = [row.expense_type for row in self.get("entries") if row.expense_type]
        if row_labels:
            parts.append(", ".join(row_labels[:3]))
            if len(row_labels) > 3:
                parts.append(f"+{len(row_labels) - 3} more")
        return " | ".join(part for part in parts if part) or "Farm Cashbook transactions"

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

    def validate_cost_center(self, cost_center, row_idx):
        company = self.get_company()
        cost_center_doc = frappe.db.get_value(
            "Cost Center",
            cost_center,
            ["name", "is_group", "company"],
            as_dict=True,
        )
        if not cost_center_doc:
            frappe.throw(f"Select a valid Cost Center on row {row_idx}.")
        if cost_center_doc.is_group:
            frappe.throw(f"Cost Center on row {row_idx} must not be a group cost center.")
        if company and cost_center_doc.company != company:
            frappe.throw(f"Cost Center on row {row_idx} must belong to company {company}.")

    def get_company(self):
        if self.farm:
            company = frappe.db.get_value("Farm", self.farm, "owner_name")
            if company:
                return company
        settings_company = frappe.db.get_single_value("Farm Management Settings", "default_company")
        return settings_company or frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
