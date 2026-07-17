import frappe
from frappe.model.document import Document


class LivestockSpecies(Document):
    def validate(self):
        expected_group = {
            "Animal Husbandry": "Livestock",
            "Poultry": "Poultry",
            "Apiculture": "Other",
        }.get(self.farm_type)
        if expected_group and self.species_group != expected_group:
            frappe.throw(
                f"Species Group must be {expected_group} for Farm Type {self.farm_type}."
            )
