import frappe
from frappe.model.document import Document
from frappe.utils import flt, today

class BiologicalAsset(Document):
    def validate(self):
        self.set_project_defaults()
        self.validate_managed_item()
        self.validate_livestock_breed()
        self.validate_mandatory_fields()
        self.recalculate_valuation()
        self.validate_quantity()

    def set_project_defaults(self):
        if not self.linked_project:
            return
        duplicate = frappe.db.get_value(
            "Biological Asset",
            {
                "linked_project": self.linked_project,
                "status": "Active",
                "name": ["!=", self.name or ""],
            },
            "name",
        )
        if duplicate:
            frappe.throw(
                f"Project {self.linked_project} is already linked to active Biological Asset {duplicate}."
            )
        project = frappe.db.get_value(
            "Project",
            self.linked_project,
            [
                "farm",
                "agriculture_project_type",
                "managed_crop_animal_species",
                "animal_breed",
                "project_quantity",
                "project_unit",
                "initial_asset_cost",
                "expected_start_date",
            ],
            as_dict=True,
        )
        if not project or not project.agriculture_project_type:
            frappe.throw("Linked Project must be an Agriculture Project.")
        project_type = frappe.db.get_value(
            "Agriculture Project Type",
            project.agriculture_project_type,
            ["farm_type", "managed_item"],
            as_dict=True,
        )
        from farm_management.farm_projects.agriculture_project import (
            get_asset_category_from_farm_type,
            get_primary_farm_activity,
        )

        activity = get_primary_farm_activity(project_type.farm_type)
        defaults = {
            "farm": project.farm,
            "farm_type": project_type.farm_type,
            "managed_item": project.managed_crop_animal_species or project_type.managed_item,
            "livestock_breed": project.animal_breed,
            "asset_category": get_asset_category_from_farm_type(activity),
            "quantity": project.project_quantity,
            "unit": project.project_unit,
            "initial_cost": project.initial_asset_cost,
            "acquisition_date": project.expected_start_date,
        }
        for fieldname, value in defaults.items():
            if value not in (None, "") and not self.get(fieldname):
                self.set(fieldname, value)

    def validate_mandatory_fields(self):
        if self.asset_category != "Crops in Growth":
            mandatory_fields = ["acquisition_date", "quantity", "unit", "initial_cost"]
            missing = [f for f in mandatory_fields if self.get(f) is None or str(self.get(f)).strip() == ""]
            if missing:
                frappe.throw(f"Mandatory fields required for {self.asset_category}: {', '.join(missing)}")
            if (
                flt(self.initial_cost) + flt(self.capitalized_cost) <= 0
                and not self.flags.get("allow_zero_initial_cost")
            ):
                frappe.throw(
                    "Initial or capitalized acquisition cost must be greater than zero. "
                    "For purchased livestock or poultry, "
                    "use Animal Stock Entry so quantity and cost are capitalized from the submitted purchase."
                )

    def validate_managed_item(self):
        if not self.farm_type or not self.managed_item:
            return
        farm_type = frappe.get_doc("Farm Type", self.farm_type)
        managed_items = {
            (row.farm_produce or "").strip().lower()
            for row in farm_type.get("managed_items", [])
            if row.farm_produce
        }
        if managed_items and self.managed_item.strip().lower() not in managed_items:
            frappe.throw(
                f"Managed item '{self.managed_item}' is not listed under Farm Type '{self.farm_type}'."
            )

    def validate_livestock_breed(self):
        if not self.livestock_breed:
            return
        breed_species = frappe.db.get_value("Livestock Breed", self.livestock_breed, "species")
        if breed_species and self.managed_item and breed_species != self.managed_item:
            frappe.throw("Breed must belong to the selected managed animal species.")

    def recalculate_valuation(self, scale_by_quantity=False):
        if scale_by_quantity and flt(self.previous_quantity):
            ratio = flt(self.quantity) / flt(self.previous_quantity)
            self.initial_cost = flt(self.initial_cost) * ratio
            self.current_fair_value = flt(self.current_fair_value) * ratio
            self.capitalized_cost = flt(self.capitalized_cost) * ratio
            self.cost_to_sell = flt(self.cost_to_sell) * ratio

        if (self.valuation_method or "Cost Accumulation") == "Cost Accumulation" or not self.current_fair_value:
            self.current_fair_value = flt(self.initial_cost) + flt(self.capitalized_cost)

        self.net_fair_value = flt(self.current_fair_value) - flt(self.cost_to_sell)
        self.accumulated_gain_loss = flt(self.net_fair_value) - flt(self.initial_cost)
        self.previous_quantity = flt(self.quantity)

    def validate_quantity(self):
        if self.status == "Harvested" and flt(self.quantity) == 0:
            return
        if self.quantity and flt(self.quantity) <= 0:
            frappe.throw("Quantity must be greater than zero.")
        if self.mortality_to_date and flt(self.mortality_to_date) > flt(self.quantity):
            frappe.throw("Mortality to date cannot exceed total quantity.")

    def on_update(self):
        self.db_set("last_valuation_date", today(), update_modified=False)

    def after_insert(self):
        opening_cost = flt(self.initial_cost)
        if not opening_cost:
            return
        frappe.db.set_value(
            self.doctype,
            self.name,
            {
                "initial_cost": 0,
                "current_fair_value": 0,
                "net_fair_value": 0,
                "accumulated_gain_loss": 0,
            },
            update_modified=False,
        )
        from farm_management.biological_assets.valuation import create_capitalization_document

        create_capitalization_document(
            biological_asset=self.name,
            amount=opening_cost,
            posting_date=self.acquisition_date,
            capitalization_type="Opening",
            source_doctype=self.doctype,
            source_name=self.name,
            project=self.linked_project,
            remarks="Initial biological asset recognition",
        )

def update_fair_values():
    from frappe.utils import add_days
    if not frappe.db.get_single_value("Farm Management Settings", "enable_fair_value_scheduler"):
        return
    cutoff = add_days(today(), -30)
    overdue = frappe.get_all("Biological Asset", filters={"status": "Active", "last_valuation_date": ["<", cutoff]}, fields=["name", "farm", "asset_name"])
    for asset in overdue:
        if frappe.db.exists(
            "ToDo",
            {
                "reference_type": "Biological Asset",
                "reference_name": asset.name,
                "status": "Open",
            },
        ):
            continue
        frappe.get_doc({"doctype": "ToDo", "description": f"Biological Asset valuation overdue: {asset.asset_name}", "reference_type": "Biological Asset", "reference_name": asset.name, "priority": "Medium"}).insert(ignore_permissions=True)
