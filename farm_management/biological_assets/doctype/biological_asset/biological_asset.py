import frappe
from frappe.model.document import Document
from frappe.utils import flt, today
from farm_management.biological_assets.valuation import create_fair_value_journal_entry

class BiologicalAsset(Document):
    def validate(self):
        self.recalculate_valuation()
        self.validate_quantity()

    def recalculate_valuation(self, scale_by_quantity=False):
        if scale_by_quantity and flt(self.previous_quantity):
            ratio = flt(self.quantity) / flt(self.previous_quantity)
            self.initial_cost = flt(self.initial_cost) * ratio
            self.current_fair_value = flt(self.current_fair_value) * ratio
            self.capitalized_cost = flt(self.capitalized_cost) * ratio
            self.cost_to_sell = flt(self.cost_to_sell) * ratio

        if (self.valuation_method or "Cost Accumulation") == "Cost Accumulation" or not self.current_fair_value:
            self.current_fair_value = flt(self.initial_cost) + flt(self.capitalized_cost)

        self.net_fair_value = flt(self.current_fair_value) - flt(self.cost_to_sell)
        self.accumulated_gain_loss = flt(self.net_fair_value) - flt(self.initial_cost)
        self.previous_quantity = flt(self.quantity)

    def validate_quantity(self):
        if self.status == "Harvested" and flt(self.quantity) == 0:
            return
        if self.quantity and flt(self.quantity) <= 0:
            frappe.throw("Quantity must be greater than zero.")
        if self.mortality_to_date and flt(self.mortality_to_date) > flt(self.quantity):
            frappe.throw("Mortality to date cannot exceed total quantity.")

    def on_update(self):
        self.db_set("last_valuation_date", today(), update_modified=False)
        create_fair_value_journal_entry(self)

def update_fair_values():
    from frappe.utils import add_days
    if not frappe.db.get_single_value("Farm Management Settings", "enable_fair_value_scheduler"):
        return
    cutoff = add_days(today(), -30)
    overdue = frappe.get_all("Biological Asset", filters={"status": "Active", "last_valuation_date": ["<", cutoff]}, fields=["name", "farm", "asset_name"])
    for asset in overdue:
        frappe.get_doc({"doctype": "ToDo", "description": f"Biological Asset valuation overdue: {asset.asset_name}", "reference_type": "Biological Asset", "reference_name": asset.name, "priority": "Medium"}).insert(ignore_permissions=True)
