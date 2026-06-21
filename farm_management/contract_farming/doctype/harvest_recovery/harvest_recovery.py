import frappe
from frappe.model.document import Document
from frappe.utils import flt

from farm_management.contract_farming.doctype.contract_farming_agreement.contract_farming_agreement import (
    update_contract_rollups,
)
from farm_management.contract_farming.accounting import cancel_journal_entry, create_harvest_recovery_journal

class HarvestRecovery(Document):
    def validate(self):
        self.validate_agreement()
        self.gross_payment = flt(self.quantity_delivered_kg) * flt(self.purchase_price_per_kg)
        self.net_payment = flt(self.gross_payment) - flt(self.loan_recovery_amount)
        if flt(self.net_payment) < 0:
            frappe.throw("Net Payment cannot be negative.")

    def validate_agreement(self):
        agreement_farmer = frappe.db.get_value("Contract Farming Agreement", self.agreement, "farmer")
        if agreement_farmer and agreement_farmer != self.farmer:
            frappe.throw("Farmer must match the selected Contract Farming Agreement.")

    def on_submit(self):
        journal_entry = create_harvest_recovery_journal(self)
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
