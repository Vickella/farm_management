import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate


class LivestockBreedingRecord(Document):
    def validate(self):
        if self.dam == self.sire:
            frappe.throw("Dam and Sire must be different animals.")
        dam = frappe.db.get_value(
            "Livestock Individual", self.dam, ["sex", "species", "farm"], as_dict=True
        )
        sire = frappe.db.get_value(
            "Livestock Individual", self.sire, ["sex", "species", "farm"], as_dict=True
        )
        if not dam or dam.sex != "Female":
            frappe.throw("Dam must be a female Livestock Individual.")
        if not sire or sire.sex != "Male":
            frappe.throw("Sire must be a male Livestock Individual.")
        if dam.species != sire.species:
            frappe.throw("Dam and Sire must belong to the same species.")
        if dam.farm != self.farm or sire.farm != self.farm:
            frappe.throw("Dam, Sire, and Breeding Record must belong to the same Farm.")
        for fieldname in ("expected_birth_date", "actual_birth_date"):
            value = self.get(fieldname)
            if value and getdate(value) < getdate(self.mating_date):
                frappe.throw(f"{self.meta.get_label(fieldname)} cannot be before Mating Date.")
        counts = (self.litter_size, self.offspring_born_alive, self.offspring_stillborn)
        if any(value is not None and flt(value) < 0 for value in counts):
            frappe.throw("Offspring counts cannot be negative.")
        if self.litter_size is not None and (
            flt(self.offspring_born_alive) + flt(self.offspring_stillborn)
            > flt(self.litter_size)
        ):
            frappe.throw("Born Alive plus Stillborn cannot exceed Litter Size.")
