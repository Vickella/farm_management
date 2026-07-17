import frappe
from frappe.model.document import Document


class LivestockBreed(Document):
    def validate(self):
        if not frappe.db.exists("Livestock Species", {"name": self.species, "is_active": 1}):
            frappe.throw("Breed must belong to an active Livestock Species.")
