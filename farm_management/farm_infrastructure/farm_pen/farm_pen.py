import frappe
from frappe.model.document import Document
from frappe.utils import flt


class FarmPen(Document):
    def validate(self):
        if flt(self.capacity) < 0 or flt(self.current_occupancy) < 0:
            frappe.throw("Capacity and current occupancy cannot be negative.")
        if flt(self.capacity) and flt(self.current_occupancy) > flt(self.capacity):
            frappe.throw("Current occupancy cannot exceed capacity.")
        self.occupancy_rate = (
            flt(self.current_occupancy) / flt(self.capacity) * 100
            if flt(self.capacity)
            else 0
        )
