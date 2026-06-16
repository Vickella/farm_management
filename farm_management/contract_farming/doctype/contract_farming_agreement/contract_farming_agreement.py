import frappe
from frappe.model.document import Document
from frappe.utils import flt

class ContractFarmingAgreement(Document):
    def validate(self):
        self.calculate_totals()

    def calculate_totals(self):
        self.total_input_loan = flt(self.seed_value) + flt(self.fertilizer_value) + flt(self.chemical_value)
        self.total_expected_purchase = flt(self.production_target_kg) * flt(self.agreed_purchase_price_per_kg)
