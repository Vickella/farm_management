from frappe.model.document import Document
from frappe.utils import flt


class HarvestRecovery(Document):
    def validate(self):
        self.gross_payment = flt(self.quantity_delivered_kg) * flt(
            self.purchase_price_per_kg
        )
        self.net_payment = self.gross_payment - flt(self.loan_recovery_amount)
