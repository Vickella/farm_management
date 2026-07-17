import frappe
from frappe.model.document import Document
from frappe.utils import flt
from farm_management.server_validation import get_farm_context, validate_farm_type_assignment


class FarmField(Document):
    def validate(self):
        if flt(self.field_size_ha) <= 0:
            frappe.throw("Field Size must be greater than zero.")
        farm = get_farm_context(self.farm, require_active=self.current_status == "Active")
        if flt(self.field_size_ha) > flt(farm.total_land_size):
            frappe.throw("Field Size cannot exceed the Farm total land size.")
        allocated = flt(
            frappe.db.sql(
                """select sum(field_size_ha) from `tabFarm Field`
                where farm=%s and name!=%s""",
                (self.farm, self.name or ""),
            )[0][0]
        )
        if allocated + flt(self.field_size_ha) > flt(farm.total_land_size):
            frappe.throw(
                "Total area across Farm Fields cannot exceed the Farm total land size."
            )
        if self.crop_assigned:
            crop_farm_type = frappe.db.get_value("Crop Type", self.crop_assigned, "category")
            if not crop_farm_type:
                frappe.throw("Current Crop must be a valid Crop Type with a Farm Type.")
            validate_farm_type_assignment(self.farm, crop_farm_type)
