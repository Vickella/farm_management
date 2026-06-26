import frappe
from frappe.model.document import Document
from frappe.utils import flt

from farm_management.biological_assets.valuation import apply_capitalization, reverse_capitalization


class BiologicalAssetCapitalization(Document):
    def validate(self):
        if not flt(self.amount) and not flt(self.quantity_delta):
            frappe.throw("Enter a capitalized amount or quantity movement.")
        if flt(self.amount) < 0:
            frappe.throw("Capitalized amount cannot be negative.")

    def on_submit(self):
        apply_capitalization(self)

    def on_cancel(self):
        reverse_capitalization(self)

@frappe.whitelist()
def calculate_amount(docname, asset):
    # Fetch costs from linked logs that haven't been capitalized yet
    # Example logic: Sum costs from Livestock Health Event and Feeding Log
    total_cost = 0.0
    
    # 1. Health Events
    health_events = frappe.get_all("Livestock Health Event", 
        filters={"biological_asset": asset, "docstatus": 1, "capitalized": 0},
        fields=["name", "cost"]
    )
    for ev in health_events:
        total_cost += flt(ev.cost)
        
    # 2. Feeding Logs
    feeding_logs = frappe.get_all("Feeding Log", 
        filters={"biological_asset": asset, "docstatus": 1, "capitalized": 0},
        fields=["name", "total_cost"]
    )
    for log in feeding_logs:
        total_cost += flt(log.total_cost)
        
    return total_cost
