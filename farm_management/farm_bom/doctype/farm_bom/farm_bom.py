import frappe
from frappe.model.document import Document
from frappe.utils import flt

class FarmBOM(Document):
    def validate(self):
        self.validate_project()
        self.validate_item_uoms()
        self.calculate_totals()

    def validate_project(self):
        if not self.project:
            frappe.throw("Project is required for a Farm BOM.")
        project_farm = frappe.db.get_value("Project", self.project, "farm")
        if self.farm and project_farm and self.farm != project_farm:
            frappe.throw("Farm BOM farm must match the selected Project farm.")

    def validate_item_uoms(self):
        for row in self.bom_items:
            if not row.item:
                continue
            stock_uom = frappe.db.get_value("Item", row.item, "stock_uom")
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
