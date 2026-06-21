import frappe
from frappe.model.document import Document
from frappe.utils import flt

from farm_management.contract_farming.doctype.contract_farming_agreement.contract_farming_agreement import (
    update_contract_rollups,
)


class InputLoanDisbursement(Document):
    def validate(self):
        if flt(self.value) <= 0:
            frappe.throw("Input loan value must be greater than zero.")
        agreement_farmer = frappe.db.get_value("Contract Farming Agreement", self.agreement, "farmer")
        if agreement_farmer and agreement_farmer != self.farmer:
            frappe.throw("Farmer must match the selected Contract Farming Agreement.")
        if self.input_type != "Cash" and not self.item:
            frappe.throw("Item is required for non-cash input loan disbursements.")
        if self.recovered and not self.recovery_date:
            frappe.throw("Recovery Date is required when the input loan is marked recovered.")

    def on_update(self):
        update_contract_rollups(self.agreement)

    def after_delete(self):
        update_contract_rollups(self.agreement)
