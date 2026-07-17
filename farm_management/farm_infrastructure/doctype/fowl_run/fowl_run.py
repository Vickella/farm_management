import frappe
from frappe.model.document import Document
from frappe.utils import flt
from farm_management.server_validation import get_farm_context, validate_farm_type_assignment


class FowlRun(Document):
    def validate(self):
        get_farm_context(self.farm, require_active=self.current_status == "Active")
        validate_farm_type_assignment(self.farm, self.bird_type)
        self.validate_managed_species()
        if self.capacity is not None and flt(self.capacity) < 0:
            frappe.throw("Capacity cannot be negative.")
        if self.current_flock_size is not None and flt(self.current_flock_size) < 0:
            frappe.throw("Current Flock Size cannot be negative.")
        if self.capacity and self.current_flock_size is not None and flt(self.current_flock_size) > flt(self.capacity):
            frappe.throw("Current Flock Size cannot exceed Capacity.")

    def validate_managed_species(self):
        if not self.bird_type or not self.managed_species:
            return
        farm_type = frappe.get_doc("Farm Type", self.bird_type)
        managed_items = {
            (row.farm_produce or "").strip().lower()
            for row in farm_type.get("managed_items", [])
            if row.farm_produce
        }
        if managed_items and self.managed_species.strip().lower() not in managed_items:
            frappe.throw(f"Managed poultry type '{self.managed_species}' is not listed under Farm Type '{self.bird_type}'.")
        species = frappe.db.get_value(
            "Livestock Species", self.managed_species, ["species_group", "is_active"], as_dict=True
        )
        if not species or not species.is_active or species.species_group != "Poultry":
            frappe.throw("Fowl Run Managed Species must be an active poultry species.")
