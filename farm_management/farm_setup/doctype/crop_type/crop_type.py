import frappe
from frappe.model.document import Document
from frappe.utils import flt


class CropType(Document):
    def validate(self):
        if self.growth_period_days is not None and flt(self.growth_period_days) <= 0:
            frappe.throw("Growth Period must be greater than zero.")
        if self.expected_yield_per_ha is not None and flt(self.expected_yield_per_ha) < 0:
            frappe.throw("Expected Yield per Hectare cannot be negative.")
        if flt(self.expected_yield_per_ha) and not self.yield_unit:
            frappe.throw("Yield Unit is required when Expected Yield is entered.")
        if self.category and not frappe.db.exists(
            "Farm Type Managed Item",
            {
                "parent": self.category,
                "parenttype": "Farm Type",
                "farm_produce_doctype": "Crop Type",
                "farm_activity": ["in", ["Crop Production", "Agroforestry"]],
            },
        ):
            frappe.throw("Crop Category must be a Farm Type configured for crop production.")
