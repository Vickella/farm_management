import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, flt, today


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

