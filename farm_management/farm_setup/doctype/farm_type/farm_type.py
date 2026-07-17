import frappe
from frappe.model.document import Document


class FarmType(Document):
    ACTIVITY_MASTER = {
        "Crop Production": "Crop Type",
        "Animal Husbandry": "Livestock Species",
        "Poultry Production": "Livestock Species",
        "Apiculture": "Livestock Species",
        "Agroforestry": "Crop Type",
    }

    def validate(self):
        self.validate_managed_items()

    def validate_managed_items(self):
        seen = set()
        for row in self.get("managed_items", []):
            expected_master = self.ACTIVITY_MASTER.get(row.farm_activity)
            if not expected_master:
                frappe.throw(f"Select a valid Farm Activity on row {row.idx}.")
            row.farm_produce_doctype = expected_master
            if not row.farm_produce:
                frappe.throw(f"Select Farm Produce on row {row.idx}.")
            if (
                not (frappe.flags.in_install or frappe.flags.in_migrate)
                and not frappe.db.exists(expected_master, row.farm_produce)
            ):
                frappe.throw(
                    f"Farm Produce on row {row.idx} must be a valid {expected_master} "
                    f"for {row.farm_activity}."
                )
            if not (frappe.flags.in_install or frappe.flags.in_migrate):
                self.validate_produce_activity(row)
            key = (row.farm_activity, row.farm_produce)
            if key in seen:
                frappe.throw(f"{row.farm_produce} is listed more than once for {row.farm_activity}.")
            seen.add(key)

        if self.name != "Mixed Farming" and not self.get("managed_items"):
            frappe.throw("Add at least one Farm Activity and Farm Produce row.")

    def validate_produce_activity(self, row):
        if row.farm_produce_doctype != "Livestock Species":
            return
        species_group = frappe.db.get_value("Livestock Species", row.farm_produce, "species_group")
        expected_group = {
            "Animal Husbandry": "Livestock",
            "Poultry Production": "Poultry",
        }.get(row.farm_activity)
        if expected_group and species_group != expected_group:
            frappe.throw(
                f"{row.farm_produce} is classified as {species_group or 'an unspecified group'} and "
                f"cannot be selected for {row.farm_activity} on row {row.idx}."
            )
