import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, flt, today


class LivestockIndividual(Document):
    def validate(self):
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
            dam_doc = frappe.get_value("Livestock Individual", self.dam, "sex")
            if dam_doc and dam_doc != "Female":
                frappe.throw("Dam must be a Female animal.")
        if self.sire:
            sire_doc = frappe.get_value("Livestock Individual", self.sire, "sex")
            if sire_doc and sire_doc not in ("Male", "Castrated"):
                frappe.throw("Sire must be a Male or Castrated animal.")

    def validate_breed_species(self):
        if not self.breed or not self.species:
            return
        breed_species = frappe.db.get_value("Livestock Breed", self.breed, "species")
        if breed_species and breed_species != self.species:
            frappe.throw("Breed must belong to the selected Species.")

    def validate_biological_asset(self):
        if not self.biological_asset:
            return
        asset = frappe.get_doc("Biological Asset", self.biological_asset)
        if self.farm and asset.farm != self.farm:
            frappe.throw("Biological Asset farm must match the animal farm.")
        species_name = frappe.db.get_value("Livestock Species", self.species, "species_name")
        if species_name and asset.managed_item and species_name != asset.managed_item:
            frappe.throw("Biological Asset managed item must match the animal species.")
