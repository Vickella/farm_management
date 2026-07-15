import frappe
from frappe.model.document import Document
from frappe.utils import flt


class FarmPond(Document):
    def validate(self):
        if self.depth_meters is not None and flt(self.depth_meters) < 0:
            frappe.throw("Depth cannot be negative.")
        if self.water_capacity_litres is not None and flt(self.water_capacity_litres) < 0:
            frappe.throw("Water Capacity cannot be negative.")
        if self.species and self.managed_species:
            farm_type = frappe.get_doc("Farm Type", self.species)
            managed_items = {
                (row.farm_produce or "").strip().lower()
                for row in farm_type.get("managed_items", [])
                if row.farm_produce
            }
            if managed_items and self.managed_species.strip().lower() not in managed_items:
                frappe.throw(f"Managed aquaculture species '{self.managed_species}' is not listed under Farm Type '{self.species}'.")
