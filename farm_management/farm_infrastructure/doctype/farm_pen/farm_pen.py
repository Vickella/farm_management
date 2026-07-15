import frappe
from frappe.model.document import Document
from frappe.utils import flt

class FarmPen(Document):
    def validate(self):
        self.validate_managed_species()
        if self.capacity is not None and flt(self.capacity) < 0:
            frappe.throw("Capacity cannot be negative.")
        if self.current_occupancy is not None and flt(self.current_occupancy) < 0:
            frappe.throw("Current Occupancy cannot be negative.")
        if self.capacity and self.current_occupancy is not None and flt(self.current_occupancy) > flt(self.capacity):
            frappe.throw("Current Occupancy cannot exceed Capacity.")
        if self.capacity and self.current_occupancy is not None:
            if self.capacity > 0:
                self.occupancy_rate = flt((self.current_occupancy / self.capacity) * 100, 2)

    def validate_managed_species(self):
        if not self.animal_type or not self.managed_species:
            return
        validate_managed_item(self.animal_type, self.managed_species)


def validate_managed_item(farm_type_name, managed_item):
    farm_type = frappe.get_doc("Farm Type", farm_type_name)
    managed_items = {
        (row.farm_produce or "").strip().lower()
        for row in farm_type.get("managed_items", [])
        if row.farm_produce
    }
    if managed_items and managed_item.strip().lower() not in managed_items:
        frappe.throw(f"Managed species '{managed_item}' is not listed under Farm Type '{farm_type_name}'.")
