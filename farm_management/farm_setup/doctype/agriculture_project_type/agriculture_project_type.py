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
