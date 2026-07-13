from frappe.model.document import Document

from farm_management.farm_projects.agriculture_project import validate_managed_item


class AgricultureProjectType(Document):
    def validate(self):
        validate_managed_item(self.farm_type, self.managed_item)
