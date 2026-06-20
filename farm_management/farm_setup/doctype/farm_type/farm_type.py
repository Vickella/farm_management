import frappe
from frappe.model.document import Document


class FarmType(Document):
    def validate(self):
        self.validate_managed_items()

    def validate_managed_items(self):
        seen = set()
        for row in self.get("managed_items", []):
            key = (row.managed_item_name or "").strip().lower()
            if not key:
                continue
            if key in seen:
                frappe.throw(f"Managed item '{row.managed_item_name}' is listed more than once.")
            seen.add(key)

        if self.category != "Mixed Farming" and not self.get("managed_items"):
            frappe.throw("Add at least one managed crop, animal, or species for this Farm Type.")
