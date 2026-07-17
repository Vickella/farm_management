import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, flt, today
from farm_management.server_validation import get_farm_context, validate_asset_context, validate_non_negative


class LivestockIndividual(Document):
    def validate(self):
        get_farm_context(self.farm, require_active=self.status == "Active")
        if self.date_of_birth and date_diff(today(), self.date_of_birth) < 0:
            frappe.throw("Date of Birth cannot be in the future.")
        validate_non_negative(self, ("birth_weight_kg", "current_weight_kg", "acquisition_cost"))
        self.calculate_age()
        self.validate_parentage()
        self.validate_breed_species()
        self.validate_biological_asset()

    def calculate_age(self):
        if self.date_of_birth:
            days = date_diff(today(), self.date_of_birth)
            self.age_months = flt(days / 30.44, 1)

    def validate_parentage(self):
        if self.dam and self.dam == self.name:
            frappe.throw("An animal cannot be its own dam.")
        if self.sire and self.sire == self.name:
            frappe.throw("An animal cannot be its own sire.")
        if self.dam:
            dam_doc = frappe.db.get_value("Livestock Individual", self.dam, ["sex", "species", "farm", "date_of_birth"], as_dict=True)
            if dam_doc and dam_doc.sex != "Female":
                frappe.throw("Dam must be a Female animal.")
            self.validate_parent_context(dam_doc, "Dam")
        if self.sire:
            sire_doc = frappe.db.get_value("Livestock Individual", self.sire, ["sex", "species", "farm", "date_of_birth"], as_dict=True)
            if sire_doc and sire_doc.sex not in ("Male", "Castrated"):
                frappe.throw("Sire must be a Male or Castrated animal.")
            self.validate_parent_context(sire_doc, "Sire")

    def validate_parent_context(self, parent, label):
        if not parent:
            frappe.throw(f"Select a valid {label}.")
        if parent.species != self.species or parent.farm != self.farm:
            frappe.throw(f"{label} must belong to the same Species and Farm.")
        if self.date_of_birth and parent.date_of_birth and parent.date_of_birth >= self.date_of_birth:
            frappe.throw(f"{label} must be older than the animal.")

    def validate_breed_species(self):
        if not self.breed or not self.species:
            return
        breed_species = frappe.db.get_value("Livestock Breed", {"name": self.breed, "is_active": 1}, "species")
        if not breed_species or breed_species != self.species:
            frappe.throw("Breed must belong to the selected Species.")

    def validate_biological_asset(self):
        if not self.biological_asset:
            return
        asset = validate_asset_context(self.biological_asset, farm=self.farm, active=self.status == "Active")
        species_name = frappe.db.get_value("Livestock Species", self.species, "species_name")
        if species_name and asset.managed_item and species_name != asset.managed_item:
            frappe.throw("Biological Asset managed item must match the animal species.")
