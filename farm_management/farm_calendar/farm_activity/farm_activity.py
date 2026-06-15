import frappe
from frappe.model.document import Document
from frappe.utils import add_days, today


class FarmActivity(Document):
    def validate(self):
        if self.status == "Completed" and not self.actual_date:
            frappe.throw("Actual Date is required when completing a Farm Activity.")
        duplicate = frappe.db.exists(
            "Farm Activity",
            {
                "farm": self.farm,
                "activity_type": self.activity_type,
                "scheduled_date": self.scheduled_date,
                "name": ["!=", self.name],
            },
        )
        if duplicate:
            frappe.throw(
                "A Farm Activity of this type already exists for this farm on the scheduled date."
            )

    def on_update(self):
        if self.assigned_to:
            frappe.get_doc(
                {
                    "doctype": "ToDo",
                    "allocated_to": self.assigned_to,
                    "reference_type": self.doctype,
                    "reference_name": self.name,
                    "description": self.activity_title,
                }
            ).insert(ignore_permissions=True)


def generate_scheduled_tasks():
    if not frappe.db.get_single_value(
        "Farm Management Settings", "enable_auto_activity_generation"
    ):
        return
    for farm in frappe.get_all(
        "Farm", filters={"operational_status": "Active"}, fields=["name"]
    ):
        _generate_activities_for_farm(farm)


def _generate_activities_for_farm(farm):
    activity_types = frappe.get_all(
        "Farm Activity Type",
        filters={"is_active": 1},
        fields=["name", "activity_name"],
        limit=5,
    )
    for activity_type in activity_types:
        exists = frappe.db.exists(
            "Farm Activity",
            {
                "farm": farm.name,
                "activity_type": activity_type.name,
                "scheduled_date": ["between", [today(), add_days(today(), 7)]],
            },
        )
        if not exists:
            doc = frappe.get_doc(
                {
                    "doctype": "Farm Activity",
                    "activity_title": activity_type.activity_name,
                    "farm": farm.name,
                    "activity_type": activity_type.name,
                    "scheduled_date": today(),
                    "status": "Scheduled",
                }
            )
            doc.insert(ignore_permissions=True)
