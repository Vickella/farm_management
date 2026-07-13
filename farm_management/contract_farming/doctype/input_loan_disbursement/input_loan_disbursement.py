import frappe
from frappe.model.document import Document
from frappe.utils import flt

from farm_management.contract_farming.doctype.contract_farming_agreement.contract_farming_agreement import (
    update_contract_rollups,
)
from farm_management.contract_farming.accounting import cancel_journal_entry, create_input_loan_journal


class InputLoanDisbursement(Document):
    def validate(self):
        self.calculate_total_value()
        self.validate_agreement()
        self.validate_inputs()
        if self.recovered and not self.recovery_date:
            frappe.throw("Recovery Date is required when the input loan is marked recovered.")

    def calculate_total_value(self):
        self.total_value = sum(flt(row.value) for row in self.get("disbursed_inputs", []))

    def validate_agreement(self):
        agreement = frappe.db.get_value(
            "Contract Farming Agreement", self.agreement, ["farmer", "status"], as_dict=True
        )
        if not agreement or agreement.status != "Active":
            frappe.throw("Input accounting requires an Active Contract Farming Agreement.")
        if agreement.farmer and agreement.farmer != self.farmer:
            frappe.throw("Farmer must match the selected Contract Farming Agreement.")

    def validate_inputs(self):
        if not self.get("disbursed_inputs"):
            frappe.throw("Add at least one disbursed input row.")
        for row in self.get("disbursed_inputs", []):
            if row.input_type != "Cash" and not row.item:
                frappe.throw(f"Item is required for non-cash input row #{row.idx}.")
            if flt(row.value) <= 0:
                frappe.throw(f"Input loan value must be greater than zero on row #{row.idx}.")
        if flt(self.total_value) <= 0:
            frappe.throw("Input loan value must be greater than zero.")

    def on_submit(self):
        journal_entry = create_input_loan_journal(self)
        if journal_entry:
            self.db_set("journal_entry", journal_entry, update_modified=False)
        update_contract_rollups(self.agreement)

    def on_cancel(self):
        cancel_journal_entry(self.journal_entry)
        update_contract_rollups(self.agreement)

    def on_update(self):
        update_contract_rollups(self.agreement)

    def after_delete(self):
        update_contract_rollups(self.agreement)
