import frappe
from frappe.model.document import Document
from frappe.utils import flt
from farm_management.server_validation import apply_project_context, validate_date_order, validate_unique_rows

class FarmBOM(Document):
    def validate(self):
        self.validate_project()
        self.validate_plan()
        self.validate_item_uoms()
        self.calculate_totals()

    def validate_project(self):
        if not self.project:
            frappe.throw("Project is required for a Farm BOM.")
        project = apply_project_context(self)
        if self.project_type and self.project_type != project.agriculture_project_type:
            frappe.throw("Farm BOM Project Type must match the selected Project.")
        self.project_type = project.agriculture_project_type
        self.farm = project.farm
        if not self.bom_title:
            self.bom_title = f"{self.project} Resource Plan"
        self.planned_quantity = self.planned_quantity or project.project_quantity
        self.planned_quantity_unit = self.planned_quantity_unit or project.project_unit
        self.planned_start_date = self.planned_start_date or project.expected_start_date
        self.planned_end_date = self.planned_end_date or project.expected_end_date

    def validate_plan(self):
        if flt(self.planned_quantity) <= 0:
            frappe.throw("Planned Quantity must be greater than zero.")
        if self.production_cycle_days is not None and flt(self.production_cycle_days) <= 0:
            frappe.throw("Production Cycle Days must be greater than zero.")
        validate_date_order(self.planned_start_date, self.planned_end_date, "Planned Start Date", "Planned End Date")
        if not self.bom_items:
            frappe.throw("Add at least one BOM Item.")
        validate_unique_rows(self.bom_items, ("item", "item_description"), "BOM Item")

    def validate_item_uoms(self):
        for row in self.bom_items:
            if flt(row.quantity) <= 0:
                frappe.throw(f"Quantity must be greater than zero on BOM row {row.idx}.")
            if flt(row.unit_cost) < 0:
                frappe.throw(f"Unit Cost cannot be negative on BOM row {row.idx}.")
            if not row.item:
                continue
            item = frappe.db.get_value("Item", row.item, ["stock_uom", "disabled"], as_dict=True)
            if not item or item.disabled:
                frappe.throw(f"Select an enabled Item on BOM row {row.idx}.")
            stock_uom = item.stock_uom
            if stock_uom and row.unit != stock_uom:
                frappe.throw(
                    f"Unit on row {row.idx} must match Item {row.item} default UOM ({stock_uom})."
                )

    def calculate_totals(self):
        total = 0
        for item in self.bom_items:
            item.total_cost = flt(item.quantity) * flt(item.unit_cost)
            total += flt(item.total_cost)
        self.total_estimated_cost = total
