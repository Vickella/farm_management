import frappe
from frappe.model.document import Document
from frappe.utils import flt

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
