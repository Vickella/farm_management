import frappe
from frappe.model.document import Document


class LivestockHealthEvent(Document):
    def validate(self):
        if self.weight_kg and self.animal:
            frappe.db.set_value(
                "Livestock Individual",
                self.animal,
                "current_weight_kg",
                self.weight_kg,
                update_modified=False,
            )

