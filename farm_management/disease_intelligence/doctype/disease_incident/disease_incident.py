import frappe
from frappe.model.document import Document


class DiseaseIncident(Document):
    def validate(self):
        if self.incident_type == "Pest" and not self.pest:
            frappe.throw("Pest is required for Pest incidents.")
        if self.incident_type == "Animal Disease" and not self.animal_disease:
            frappe.throw("Animal Disease is required for Animal Disease incidents.")
        if self.resolved and not self.resolution_date:
            frappe.throw("Resolution Date is required when an incident is resolved.")
