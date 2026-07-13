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
        self.quantity_delivered = flt(self.quantity_delivered) or flt(
            self.quantity_delivered_kg
        )
        self.purchase_price_per_unit = flt(self.purchase_price_per_unit) or flt(
            self.purchase_price_per_kg
        )
        if flt(self.quantity_delivered) <= 0:
            frappe.throw("Quantity Delivered must be greater than zero.")
        if flt(self.purchase_price_per_unit) < 0:
            frappe.throw("Purchase Price Per Unit cannot be negative.")
        self.gross_payment = flt(self.quantity_delivered) * flt(
            self.purchase_price_per_unit
        )
        self.net_payment = flt(self.gross_payment) - flt(self.loan_recovery_amount)
        if flt(self.net_payment) < 0:
            frappe.throw("Net Payment cannot be negative.")
        disbursed = flt(
            frappe.db.get_value(
                "Input Loan Disbursement",
                {"agreement": self.agreement, "docstatus": 1},
                "sum(total_value)",
            )
        )
        recovered = flt(
            frappe.db.get_value(
                "Harvest Recovery",
                {
                    "agreement": self.agreement,
                    "docstatus": 1,
                    "name": ["!=", self.name or ""],
                },
                "sum(loan_recovery_amount)",
            )
        )
        if flt(self.loan_recovery_amount) > max(disbursed - recovered, 0):
            frappe.throw("Loan Recovery Amount exceeds the outstanding contract input balance.")

    def validate_agreement(self):
        agreement = frappe.db.get_value(
            "Contract Farming Agreement", self.agreement, ["farmer", "status"], as_dict=True
        )
        if not agreement or agreement.status != "Active":
            frappe.throw("Harvest accounting requires an Active Contract Farming Agreement.")
        if agreement.farmer and agreement.farmer != self.farmer:
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
