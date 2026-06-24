import frappe
from frappe.model.document import Document
from frappe.utils import flt

class ContractFarmingAgreement(Document):
    def validate(self):
        self.validate_dates()
        self.calculate_totals()

    def validate_dates(self):
        if self.contract_end_date and self.contract_start_date and self.contract_end_date <= self.contract_start_date:
            frappe.throw("Contract End Date must be after Contract Start Date.")

    def calculate_totals(self):
        self.total_input_loan = sum(flt(row.value) for row in self.get("inputs_provided", []))
        self.total_expected_purchase = flt(self.production_target) * flt(self.agreed_purchase_price_per_unit)
        self.actual_inputs_disbursed = flt(
            frappe.db.get_value(
                "Input Loan Disbursement",
                {"agreement": self.name, "docstatus": ["!=", 2]},
                "sum(value)",
            )
        )
        self.harvest_recovery_value = flt(
            frappe.db.get_value(
                "Harvest Recovery",
                {"agreement": self.name, "docstatus": ["!=", 2]},
                "sum(loan_recovery_amount)",
            )
        )
        self.net_contract_position = flt(self.actual_inputs_disbursed) - flt(self.harvest_recovery_value)


def update_contract_rollups(agreement):
    if not agreement or not frappe.db.exists("Contract Farming Agreement", agreement):
        return
    doc = frappe.get_doc("Contract Farming Agreement", agreement)
    doc.calculate_totals()
    frappe.db.set_value(
        "Contract Farming Agreement",
        agreement,
        {
            "actual_inputs_disbursed": doc.actual_inputs_disbursed,
            "harvest_recovery_value": doc.harvest_recovery_value,
            "net_contract_position": doc.net_contract_position,
        },
        update_modified=False,
    )
