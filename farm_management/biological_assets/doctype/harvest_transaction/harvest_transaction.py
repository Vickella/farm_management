import frappe
from frappe.model.document import Document
from frappe.utils import flt
from farm_management.server_validation import get_farm_context, validate_asset_context, validate_date_order

from farm_management.biological_assets.valuation import (
    get_biological_asset_account,
    get_asset_valuation_snapshot,
    reduce_asset_quantity,
    restore_asset_quantity,
)


class HarvestTransaction(Document):
    def validate(self):
        self.validate_asset()
        self.set_defaults()
        self.calculate_asset_impact()

    def validate_asset(self):
        if flt(self.quantity_harvested) <= 0:
            frappe.throw("Quantity harvested must be greater than zero.")
        asset = frappe.get_doc("Biological Asset", self.biological_asset)
        validate_asset_context(asset.name, farm=self.farm, active=True)
        validate_date_order(asset.acquisition_date, self.harvest_date, "Asset Acquisition Date", "Harvest Date")
        if asset.farm != self.farm:
            frappe.throw("Harvest farm must match the Biological Asset farm.")
        if asset.status != "Active":
            frappe.throw("Only Active Biological Assets can be harvested.")
        if asset.asset_category != "Crops in Growth":
            frappe.throw("Use Animal Stock Entry for live-animal sale, death, or issue movements.")
        if not self.conversion_item:
            frappe.throw("Conversion Item is required so harvested produce is recognized in ERPNext inventory.")
        if asset.output_item and self.conversion_item != asset.output_item:
            frappe.throw(
                f"Harvested Item must be the Biological Asset output Item {asset.output_item}."
            )
        if self.source_harvest_log:
            duplicate = frappe.db.exists(
                "Harvest Transaction",
                {
                    "source_harvest_log": self.source_harvest_log,
                    "docstatus": ["<", 2],
                    "name": ["!=", self.name or ""],
                },
            )
            if duplicate:
                frappe.throw("This Harvest Log already has an active Harvest Transaction.")
        if asset.asset_category != "Crops in Growth" and flt(asset.quantity) > 0 and flt(self.quantity_harvested) > flt(asset.quantity):
            frappe.throw("Harvest quantity cannot exceed Biological Asset quantity.")

    def set_defaults(self):
        settings = frappe.get_single("Farm Management Settings")
        farm = get_farm_context(self.farm)
        if not self.company:
            self.company = farm.owner_name or settings.default_company or frappe.defaults.get_user_default("Company")
        if farm.owner_name and self.company != farm.owner_name:
            frappe.throw("Harvest Transaction Company must match the Farm Owner Company.")
        if self.conversion_item and not self.company:
            frappe.throw("Set Company or configure Default Company in Farm Management Settings.")
        if self.conversion_item and not self.target_warehouse:
            self.target_warehouse = settings.default_harvest_warehouse
        if self.conversion_item and not self.target_warehouse:
            frappe.throw("Set Target Warehouse or configure Default Harvest Warehouse in Farm Management Settings.")
        if self.conversion_item:
            item = frappe.db.get_value("Item", self.conversion_item, ["stock_uom", "disabled", "is_stock_item"], as_dict=True)
            if not item or item.disabled or not item.is_stock_item:
                frappe.throw("Conversion Item must be an enabled stock Item.")
            self.unit = item.stock_uom
            self.validate_stock_conversion()

    def validate_stock_conversion(self):
        item_uom = frappe.db.get_value("Item", self.conversion_item, "stock_uom")
        if item_uom and self.unit != item_uom:
            frappe.throw(
                f"Harvest Unit must match conversion Item {self.conversion_item} stock UOM ({item_uom})."
            )
        warehouse_company = frappe.db.get_value(
            "Warehouse", self.target_warehouse, ["company", "is_group", "disabled"], as_dict=True
        )
        if not warehouse_company or warehouse_company.is_group or warehouse_company.disabled:
            frappe.throw("Target Warehouse must be an enabled non-group Warehouse.")
        if warehouse_company.company and self.company and warehouse_company.company != self.company:
            frappe.throw("Target Warehouse must belong to the Harvest Transaction company.")

    def calculate_asset_impact(self):
        asset = frappe.get_doc("Biological Asset", self.biological_asset)
        self.asset_quantity_before = flt(asset.quantity)
        self.asset_quantity_reduction = (
            flt(asset.quantity)
            if asset.asset_category == "Crops in Growth"
            else flt(self.quantity_harvested)
        )
        self.asset_quantity_after = max(
            flt(asset.quantity) - flt(self.asset_quantity_reduction), 0
        )
        if asset.asset_category != "Crops in Growth" and flt(asset.quantity):
            self.asset_value_reduction = flt(asset.net_fair_value) * flt(self.quantity_harvested) / flt(asset.quantity)
        else:
            self.asset_value_reduction = flt(asset.net_fair_value)
        if not self.harvest_value:
            self.harvest_value = self.asset_value_reduction
        if abs(flt(self.harvest_value) - flt(self.asset_value_reduction)) > 0.01:
            frappe.throw(
                "Harvest Value must equal the Biological Asset carrying value being transferred. "
                "Submit a Biological Asset Valuation first if fair value changed at harvest."
            )

    def on_submit(self):
        self.db_set(
            "valuation_snapshot",
            get_asset_valuation_snapshot(self.biological_asset),
            update_modified=False,
        )
        self.asset_value_reduction = reduce_asset_quantity(
            self.biological_asset,
            self.asset_quantity_reduction,
            source_doctype=self.doctype,
            source_name=self.name,
        )
        if self.conversion_item and not self.stock_entry:
            asset = frappe.get_doc("Biological Asset", self.biological_asset)
            biological_asset_account = get_biological_asset_account(asset)
            if not biological_asset_account:
                frappe.throw(
                    "Configure the Biological Asset Account for this managed item before harvesting to stock."
                )
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
                    "basic_rate": flt(self.harvest_value) / flt(self.quantity_harvested),
                    "allow_zero_valuation_rate": 0,
                    "expense_account": biological_asset_account,
                    "project": asset.linked_project,
                    "t_warehouse": self.target_warehouse,
                },
            )
            se.insert(ignore_permissions=True)
            se.submit()
            self.db_set("stock_entry", se.name)
            self.db_set("asset_value_reduction", self.asset_value_reduction, update_modified=False)
            asset.db_set("last_posted_net_fair_value", asset.net_fair_value, update_modified=False)

    def on_cancel(self):
        if self.stock_entry and frappe.db.exists("Stock Entry", self.stock_entry):
            stock_entry = frappe.get_doc("Stock Entry", self.stock_entry)
            if stock_entry.docstatus == 1:
                stock_entry.cancel()
        asset_category = frappe.db.get_value(
            "Biological Asset", self.biological_asset, "asset_category"
        )
        quantity_reduction = flt(self.asset_quantity_reduction)
        if not quantity_reduction:
            quantity_reduction = (
                flt(self.asset_quantity_before)
                if asset_category == "Crops in Growth"
                else flt(self.quantity_harvested)
            )
        restore_asset_quantity(
            self.biological_asset,
            quantity_reduction,
            self.asset_value_reduction,
            source_doctype=self.doctype,
            source_name=self.name,
            valuation_snapshot=self.valuation_snapshot,
        )
