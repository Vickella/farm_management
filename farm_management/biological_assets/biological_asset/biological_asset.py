import frappe
from frappe.model.document import Document
from frappe.utils import flt, today

class BiologicalAsset(Document):
    def validate(self):
        self.calculate_net_fair_value()
        self.validate_quantity()

    def calculate_net_fair_value(self):
        if self.current_fair_value and self.cost_to_sell:
            self.net_fair_value = flt(self.current_fair_value) - flt(self.cost_to_sell)
            self.accumulated_gain_loss = flt(self.net_fair_value) - flt(self.initial_cost)

    def validate_quantity(self):
        if self.quantity and flt(self.quantity) <= 0:
            frappe.throw("Quantity must be greater than zero.")
        if self.mortality_to_date and flt(self.mortality_to_date) > flt(self.quantity):
            frappe.throw("Mortality to date cannot exceed total quantity.")

    def on_update(self):
        self.db_set("last_valuation_date", today(), update_modified=False)

def update_fair_values():
    from frappe.utils import add_days
    cutoff = add_days(today(), -30)
    overdue = frappe.get_all("Biological Asset", filters={"status": "Active", "last_valuation_date": ["<", cutoff]}, fields=["name", "farm", "asset_name"])
    for asset in overdue:
        frappe.get_doc({"doctype": "ToDo", "description": f"Biological Asset valuation overdue: {asset.asset_name}", "reference_type": "Biological Asset", "reference_name": asset.name, "priority": "Medium"}).insert(ignore_permissions=True)
