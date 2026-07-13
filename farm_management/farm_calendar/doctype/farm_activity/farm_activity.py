import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, flt, today

from farm_management.biological_assets.valuation import (
    create_capitalization_document,
    get_capitalization_source_account,
)


class FarmActivity(Document):
    def validate(self):
        self.validate_capitalization_immutability()
        if self.status == "Completed" and not self.actual_date:
            self.actual_date = today()
        if self.status == "Completed" and self.actual_cost is None:
            frappe.throw("Actual Cost is required when completing a Farm Activity.")
        if self.capitalizable and not self.biological_asset:
            frappe.throw("Select a Biological Asset when marking an activity as capitalizable.")
        if (
            self.capitalizable
            and self.status == "Completed"
            and flt(self.actual_cost)
            and not self.capitalized_to_asset
        ):
            self.capitalization_credit_account = get_capitalization_source_account(
                self.biological_asset,
                self.capitalization_source_doctype,
                self.capitalization_source,
                self.actual_cost,
                project=self.project,
            )

    def validate_capitalization_immutability(self):
        previous = self.get_doc_before_save()
        if not previous or not previous.capitalized_to_asset:
            return
        protected = (
            "status",
            "actual_date",
            "actual_cost",
            "biological_asset",
            "project",
            "capitalization_source_doctype",
            "capitalization_source",
        )
        if any(previous.get(fieldname) != self.get(fieldname) for fieldname in protected):
            frappe.throw("Cancel the linked Biological Asset Capitalization before changing posted activity costs.")

    def on_update(self):
        if (
            self.status == "Completed"
            and self.capitalizable
            and self.biological_asset
            and flt(self.actual_cost)
            and not self.capitalized_to_asset
        ):
            capitalization = create_capitalization_document(
                biological_asset=self.biological_asset,
                amount=self.actual_cost,
                posting_date=self.actual_date,
                capitalization_type="Farm Activity",
                source_doctype=self.doctype,
                source_name=self.name,
                remarks=f"Capitalized farm activity: {self.activity_title}",
                project=self.project,
                credit_account=self.capitalization_credit_account,
                accounting_source_doctype=self.capitalization_source_doctype,
                accounting_source_name=self.capitalization_source,
            )
            self.db_set("capitalization", capitalization, update_modified=False)
            self.db_set("capitalized_to_asset", 1, update_modified=False)

    def on_trash(self):
        if self.capitalization and frappe.db.exists("Biological Asset Capitalization", self.capitalization):
            capitalization = frappe.get_doc("Biological Asset Capitalization", self.capitalization)
            if capitalization.docstatus == 1:
                capitalization.cancel()

def generate_scheduled_tasks():
    if not frappe.db.get_single_value(
        "Farm Management Settings", "enable_auto_activity_generation"
    ):
        return

    frequency_days = {"Daily": 1, "Weekly": 7, "Fortnightly": 14, "Monthly": 30}
    activity_types = frappe.get_all(
        "Farm Activity Type",
        filters={"is_active": 1, "default_frequency": ["in", list(frequency_days)]},
        fields=["name", "activity_name", "farm_category", "default_frequency"],
    )
    farms = frappe.get_all(
        "Farm", filters={"operational_status": "Active"}, fields=["name"]
    )

    for farm in farms:
        categories = get_farm_activity_categories(farm.name)
        for activity_type in activity_types:
            if categories and activity_type.farm_category not in categories:
                continue
            last_date = frappe.db.get_value(
                "Farm Activity",
                {"farm": farm.name, "activity_type": activity_type.name},
                "scheduled_date",
                order_by="scheduled_date desc",
            )
            if last_date and date_diff(today(), last_date) < frequency_days[activity_type.default_frequency]:
                continue
            frappe.get_doc(
                {
                    "doctype": "Farm Activity",
                    "activity_title": activity_type.activity_name,
                    "farm": farm.name,
                    "activity_type": activity_type.name,
                    "scheduled_date": today(),
                    "status": "Scheduled",
                }
            ).insert(ignore_permissions=True)


def get_farm_activity_categories(farm):
    category_map = {
        "Crop Production": "Crop Farming",
        "Horticulture": "Crop Farming",
        "Agroforestry": "Crop Farming",
        "Animal Husbandry": "Livestock",
        "Poultry": "Poultry",
        "Aquaculture": "Aquaculture",
    }
    farm_types = frappe.get_all(
        "Farm Type Multiselect",
        filters={"parent": farm, "parenttype": "Farm"},
        pluck="farm_type",
    )
    categories = set()
    for farm_type in farm_types:
        category = frappe.db.get_value("Farm Type", farm_type, "category")
        if category in category_map:
            categories.add(category_map[category])
    return categories
