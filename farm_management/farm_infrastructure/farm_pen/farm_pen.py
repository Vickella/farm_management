import frappe
from frappe.model.document import Document
from frappe.utils import flt

class FarmPen(Document):
    def validate(self):
        if self.capacity and self.current_occupancy is not None:
            if self.capacity > 0:
                self.occupancy_rate = flt((self.current_occupancy / self.capacity) * 100, 2)
