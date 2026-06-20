import frappe
from frappe.model.document import Document
from frappe.utils import flt

class FarmPen(Document):
    def validate(self):
        if self.capacity is not None and flt(self.capacity) < 0:
            frappe.throw("Capacity cannot be negative.")
        if self.current_occupancy is not None and flt(self.current_occupancy) < 0:
            frappe.throw("Current Occupancy cannot be negative.")
        if self.capacity and self.current_occupancy is not None and flt(self.current_occupancy) > flt(self.capacity):
            frappe.throw("Current Occupancy cannot exceed Capacity.")
        if self.capacity and self.current_occupancy is not None:
            if self.capacity > 0:
                self.occupancy_rate = flt((self.current_occupancy / self.capacity) * 100, 2)
