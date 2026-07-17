import frappe
from frappe.model.document import Document

from farm_management.farm_projects.agriculture_project import validate_managed_item


class AgricultureProjectType(Document):
    def validate(self):
        validate_managed_item(self.farm_type, self.managed_item)
        if self.farm_type == "Poultry" and not self.managed_item:
            frappe.throw(
                "Select the poultry Farm Produce. Use a specific project type such as "
                "Broiler Production, Layer Production, or Road Runner Production."
            )
        if not (frappe.flags.in_install or frappe.flags.in_migrate):
            self.validate_output_item()

    def validate_output_item(self):
        if not self.output_item:
            if self.managed_item:
                frappe.throw("Select the Expected Output Item for this Project Type.")
            return
        item = frappe.db.get_value(
            "Item",
            self.output_item,
            ["disabled", "is_stock_item", "stock_uom"],
            as_dict=True,
        )
        if not item or item.disabled or not item.is_stock_item or not item.stock_uom:
            frappe.throw(
                "Expected Output Item must be an enabled stock Item with a Stock UOM."
            )
