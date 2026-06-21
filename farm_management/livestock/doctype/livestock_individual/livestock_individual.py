import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, flt, today
from farm_management.biological_assets.valuation import (
    create_capitalization_document,
    get_or_create_biological_asset_for_livestock,
)


class LivestockIndividual(Document):
    def validate(self):
        self.calculate_age()
        self.validate_parentage()
        self.validate_breed_species()

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

    def after_insert(self):
        self.capitalize_to_biological_asset()

    def on_update(self):
        self.capitalize_to_biological_asset()

    def capitalize_to_biological_asset(self):
        if self.capitalized_to_asset:
            return

        biological_asset = get_or_create_biological_asset_for_livestock(self)
        amount = flt(self.capitalization_value) or flt(self.purchase_price)
        capitalization = create_capitalization_document(
            biological_asset=biological_asset,
            amount=amount,
            capitalization_type="Birth" if self.acquisition_type == "Born on Farm" else "Purchase",
            source_doctype=self.doctype,
            source_name=self.name,
            remarks=f"{self.acquisition_type or 'Livestock'} added to biological asset",
            quantity_delta=1,
        )
        if capitalization:
            frappe.db.set_value(
                self.doctype,
                self.name,
                {
                    "biological_asset": biological_asset,
                    "capitalized_to_asset": 1,
                },
                update_modified=False,
            )
