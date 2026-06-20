import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, flt, today
from farm_management.biological_assets.valuation import capitalize_asset_cost


class LivestockIndividual(Document):
    def validate(self):
        self.calculate_age()
        self.validate_parentage()

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

    def after_insert(self):
        self.capitalize_to_biological_asset()

    def capitalize_to_biological_asset(self):
        if not self.capitalize_to_asset or not self.biological_asset or self.capitalized_to_asset:
            return

        amount = flt(self.capitalization_value) or flt(self.purchase_price)
        capitalize_asset_cost(
            self.biological_asset,
            amount,
            source_doctype=self.doctype,
            source_name=self.name,
            remarks=f"{self.acquisition_type or 'Livestock'} added to biological asset",
            quantity_delta=1,
        )
        self.db_set("capitalized_to_asset", 1, update_modified=False)
