import frappe
from frappe.model.document import Document
from frappe.utils import flt

from farm_management.biological_assets.valuation import reduce_asset_quantity, restore_asset_quantity


class HarvestTransaction(Document):
    def validate(self):
        self.validate_asset()
        self.set_defaults()
        self.calculate_asset_impact()

    def validate_asset(self):
        if flt(self.quantity_harvested) <= 0:
            frappe.throw("Quantity harvested must be greater than zero.")
        asset = frappe.get_doc("Biological Asset", self.biological_asset)
        if asset.farm != self.farm:
            frappe.throw("Harvest farm must match the Biological Asset farm.")
        if asset.status != "Active":
            frappe.throw("Only Active Biological Assets can be harvested.")
        if asset.asset_category != "Crops in Growth" and flt(asset.quantity) > 0 and flt(self.quantity_harvested) > flt(asset.quantity):
            frappe.throw("Harvest quantity cannot exceed Biological Asset quantity.")

    def set_defaults(self):
        settings = frappe.get_single("Farm Management Settings")
        if not self.company:
            self.company = settings.default_company or frappe.defaults.get_user_default("Company")
        if self.conversion_item and not self.company:
            frappe.throw("Set Company or configure Default Company in Farm Management Settings.")
        if self.conversion_item and not self.target_warehouse:
            self.target_warehouse = settings.default_harvest_warehouse
        if self.conversion_item and not self.target_warehouse:
            frappe.throw("Set Target Warehouse or configure Default Harvest Warehouse in Farm Management Settings.")

    def calculate_asset_impact(self):
        asset = frappe.get_doc("Biological Asset", self.biological_asset)
        self.asset_quantity_before = flt(asset.quantity)
        self.asset_quantity_after = flt(asset.quantity) - flt(self.quantity_harvested)
        if asset.asset_category != "Crops in Growth" and flt(asset.quantity):
            self.asset_value_reduction = flt(asset.net_fair_value) * flt(self.quantity_harvested) / flt(asset.quantity)
        else:
            self.asset_value_reduction = flt(asset.net_fair_value)

    def on_submit(self):
        self.asset_value_reduction = reduce_asset_quantity(
            self.biological_asset,
            self.quantity_harvested,
            source_doctype=self.doctype,
            source_name=self.name,
        )
        if self.conversion_item and not self.stock_entry:
            se = frappe.new_doc("Stock Entry")
            se.stock_entry_type = "Material Receipt"
            se.company = self.company
            se.posting_date = self.harvest_date
            se.append(
                "items",
                {
                    "item_code": self.conversion_item,
                    "qty": self.quantity_harvested,
                    "uom": self.unit,
                    "basic_rate": (flt(asset.net_fair_value) / flt(self.quantity_harvested)) if asset.net_fair_value else (self.harvest_value or 0),
                    "t_warehouse": self.target_warehouse,
                },
            )
            se.insert(ignore_permissions=True)
            se.submit()
            self.db_set("stock_entry", se.name)
            self.db_set("asset_value_reduction", self.asset_value_reduction, update_modified=False)

    def on_cancel(self):
        if self.stock_entry and frappe.db.exists("Stock Entry", self.stock_entry):
            stock_entry = frappe.get_doc("Stock Entry", self.stock_entry)
            if stock_entry.docstatus == 1:
                stock_entry.cancel()
        restore_asset_quantity(
            self.biological_asset,
            self.quantity_harvested,
            self.asset_value_reduction,
            source_doctype=self.doctype,
            source_name=self.name,
        )
