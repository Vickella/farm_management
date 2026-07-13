import frappe
from frappe.model.document import Document


class FarmType(Document):
    def validate(self):
        self.validate_managed_items()

    def validate_managed_items(self):
        seen = set()
        for row in self.get("managed_items", []):
            self.set_managed_item_master(row)
            key = (row.managed_item_name or "").strip().lower()
            if not key:
                continue
            if key in seen:
                frappe.throw(f"Managed item '{row.managed_item_name}' is listed more than once.")
            seen.add(key)

        if self.category != "Mixed Farming" and not self.get("managed_items"):
            frappe.throw("Add at least one managed crop, animal, or species for this Farm Type.")

    def set_managed_item_master(self, row):
        if row.managed_item_type == "Crop":
            row.crop_type = row.crop_type or frappe.db.exists("Crop Type", row.managed_item_name)
            if row.crop_type:
                row.managed_item_name = row.crop_type
            elif not (frappe.flags.in_install or frappe.flags.in_migrate):
                frappe.throw(f"Select a Crop Type on row {row.idx}.")
        elif row.managed_item_type in ("Animal Species", "Poultry", "Aquaculture Species"):
            row.livestock_species = row.livestock_species or frappe.db.exists(
                "Livestock Species", row.managed_item_name
            )
            if row.livestock_species:
                row.managed_item_name = row.livestock_species
            elif not (frappe.flags.in_install or frappe.flags.in_migrate):
                frappe.throw(f"Select an Animal / Species on row {row.idx}.")
        elif row.managed_item_type in ("Apiary", "Other"):
            row.other_managed_item_name = (
                row.other_managed_item_name or row.managed_item_name
            )
            row.managed_item_name = row.other_managed_item_name
