import frappe
from frappe.model.document import Document
from farm_management.server_validation import get_farm_context, validate_asset_context, validate_date_order, validate_non_negative


class DiseaseIncident(Document):
    def validate(self):
        get_farm_context(self.farm)
        if self.incident_type == "Pest" and not self.pest:
            frappe.throw("Pest is required for Pest incidents.")
        if self.incident_type == "Animal Disease" and not self.animal_disease:
            frappe.throw("Animal Disease is required for Animal Disease incidents.")
        if self.resolved and not self.resolution_date:
            frappe.throw("Resolution Date is required when an incident is resolved.")
        validate_date_order(self.incident_date, self.resolution_date, "Incident Date", "Resolution Date")
        validate_non_negative(self, ("treatment_cost", "loss_estimate"))
        if self.biological_asset:
            validate_asset_context(self.biological_asset, farm=self.farm)
        if self.livestock_individual:
            if frappe.db.get_value("Livestock Individual", self.livestock_individual, "farm") != self.farm:
                frappe.throw("Livestock Individual must belong to the incident Farm.")
        if self.farm_field:
            if frappe.db.get_value("Farm Field", self.farm_field, "farm") != self.farm:
                frappe.throw("Farm Field must belong to the incident Farm.")
        if self.incident_type == "Pest":
            self.animal_disease = None
            self.livestock_individual = None
        else:
            self.pest = None
            self.farm_field = None
