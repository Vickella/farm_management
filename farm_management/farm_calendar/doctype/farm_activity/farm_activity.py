import frappe
from frappe.model.document import Document
from frappe.utils import flt, today

from farm_management.biological_assets.valuation import create_capitalization_document


class FarmActivity(Document):
    def validate(self):
        if self.status == "Completed" and not self.actual_date:
            self.actual_date = today()
        if self.status == "Completed" and self.actual_cost is None:
            frappe.throw("Actual Cost is required when completing a Farm Activity.")
        if self.capitalizable and not self.biological_asset:
            frappe.throw("Select a Biological Asset when marking an activity as capitalizable.")

    def on_update(self):
        if (
            self.status == "Completed"
            and self.capitalizable
            and self.biological_asset
            and flt(self.actual_cost)
            and not self.capitalized_to_asset
        ):
            create_capitalization_document(
                biological_asset=self.biological_asset,
                amount=self.actual_cost,
                capitalization_type="Farm Activity",
                source_doctype=self.doctype,
                source_name=self.name,
                remarks=f"Capitalized farm activity: {self.activity_title}",
                project=self.project,
            )
            self.db_set("capitalized_to_asset", 1, update_modified=False)

def generate_scheduled_tasks():
    return None
