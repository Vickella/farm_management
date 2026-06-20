import frappe
from frappe.model.document import Document
from frappe.utils import flt


class FowlRun(Document):
    def validate(self):
        if self.capacity is not None and flt(self.capacity) < 0:
            frappe.throw("Capacity cannot be negative.")
        if self.current_flock_size is not None and flt(self.current_flock_size) < 0:
            frappe.throw("Current Flock Size cannot be negative.")
        if self.capacity and self.current_flock_size is not None and flt(self.current_flock_size) > flt(self.capacity):
            frappe.throw("Current Flock Size cannot exceed Capacity.")
