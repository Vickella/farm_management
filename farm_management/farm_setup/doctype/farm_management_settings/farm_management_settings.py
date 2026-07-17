from frappe.model.document import Document

import frappe


class FarmManagementSettings(Document):
    def validate(self):
        if not self.default_company:
            configured = [
                self.meta.get_field(fieldname).label
                for fieldname in (
                    "default_cost_center",
                    "default_harvest_warehouse",
                    "biological_asset_sales_receivable_account",
                    "biological_asset_sales_income_account",
                    "biological_asset_cost_of_sales_account",
                )
                if self.get(fieldname)
            ]
            if configured:
                frappe.throw(
                    "Set Default Company before configuring: " + ", ".join(configured)
                )
            return
        self.validate_company_link("default_cost_center", "Cost Center")
        self.validate_company_link("default_harvest_warehouse", "Warehouse")
        for fieldname in (
            "biological_asset_sales_receivable_account",
            "biological_asset_sales_income_account",
            "biological_asset_cost_of_sales_account",
        ):
            self.validate_company_link(fieldname, "Account", reject_groups=True)

    def validate_company_link(self, fieldname, doctype, reject_groups=False):
        value = self.get(fieldname)
        if not value:
            return
        label = self.meta.get_field(fieldname).label
        fields = ["company"]
        if reject_groups:
            fields.append("is_group")
        linked = frappe.db.get_value(doctype, value, fields, as_dict=True)
        if not linked:
            frappe.throw(f"Select a valid {label}.")
        if linked.company != self.default_company:
            frappe.throw(
                f"{label} must belong to company {self.default_company}."
            )
        if reject_groups and linked.is_group:
            frappe.throw(f"{label} must be a ledger account.")
