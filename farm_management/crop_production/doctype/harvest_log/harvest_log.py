import frappe
from frappe.model.document import Document
from frappe.utils import flt
from farm_management.server_validation import apply_project_context, validate_asset_context, validate_date_order


class HarvestLog(Document):
    def validate(self):
        self.set_project_defaults()
        self.set_item_defaults()
        if flt(self.harvested_quantity) <= 0:
            frappe.throw("Harvested Quantity must be greater than zero.")
        if flt(self.harvest_fair_value) <= 0:
            frappe.throw("Harvest Fair Value must be greater than zero.")
        asset = validate_asset_context(self.biological_asset, farm=self.farm, project=self.project, active=True)
        validate_date_order(asset.acquisition_date, self.date, "Asset Acquisition Date", "Harvest Date")
        if self.harvest_transaction and frappe.db.exists(
            "Harvest Transaction", {"name": self.harvest_transaction, "docstatus": ["<", 2]}
        ):
            frappe.throw("This Harvest Log already has an active Harvest Transaction.")

    def set_project_defaults(self):
        if not self.project:
            return
        project = apply_project_context(self)
        if project.managed_item_doctype != "Crop Type":
            frappe.throw("Harvest Log requires a crop Agriculture Project.")
        asset = project.biological_asset
        if asset:
            asset_state = frappe.db.get_value(
                "Biological Asset", asset, ["status", "asset_category"], as_dict=True
            )
            if (
                not asset_state
                or asset_state.status != "Active"
                or asset_state.asset_category != "Crops in Growth"
            ):
                asset = None
        asset = asset or frappe.db.get_value(
            "Biological Asset",
            {"linked_project": self.project, "status": "Active", "asset_category": "Crops in Growth"},
            "name",
        )
        if not asset:
            frappe.throw(f"Project {self.project} has no active crop Biological Asset.")
        self.biological_asset = asset
        asset_farm = frappe.db.get_value("Biological Asset", asset, "farm")
        if self.farm != asset_farm:
            frappe.throw("Project, Farm, and Biological Asset must belong to the same harvest.")

    def set_item_defaults(self):
        if not self.conversion_item:
            return
        self.harvest_uom = frappe.db.get_value("Item", self.conversion_item, "stock_uom")
        if not self.harvest_uom:
            frappe.throw("The Harvested Item must have a Stock UOM.")

    def on_submit(self):
        self.create_harvest_valuation()
        transaction = frappe.get_doc(
            {
                "doctype": "Harvest Transaction",
                "farm": self.farm,
                "biological_asset": self.biological_asset,
                "harvest_date": self.date,
                "quantity_harvested": self.harvested_quantity,
                "unit": self.harvest_uom,
                "harvest_value": self.harvest_fair_value,
                "conversion_item": self.conversion_item,
                "target_warehouse": self.target_warehouse,
                "source_harvest_log": self.name,
            }
        )
        transaction.insert(ignore_permissions=True)
        transaction.submit()
        self.db_set("harvest_transaction", transaction.name, update_modified=False)
        self.db_set("status", "Completed", update_modified=False)

    def create_harvest_valuation(self):
        asset = frappe.get_doc("Biological Asset", self.biological_asset)
        if abs(flt(asset.net_fair_value) - flt(self.harvest_fair_value)) <= 0.01:
            return
        valuation = frappe.get_doc(
            {
                "doctype": "Biological Asset Valuation",
                "biological_asset": asset.name,
                "valuation_date": self.date,
                "valuation_method": "Manual Fair Value",
                "current_fair_value": self.harvest_fair_value,
                "cost_to_sell": 0,
                "valuation_basis": f"Fair value at harvest from Harvest Log {self.name}",
                "post_journal_entry": 1,
            }
        )
        valuation.insert(ignore_permissions=True)
        valuation.submit()
        self.db_set("biological_asset_valuation", valuation.name, update_modified=False)

    def on_cancel(self):
        if self.harvest_transaction and frappe.db.exists("Harvest Transaction", self.harvest_transaction):
            transaction = frappe.get_doc("Harvest Transaction", self.harvest_transaction)
            if transaction.docstatus == 1:
                transaction.cancel()
        if self.biological_asset_valuation and frappe.db.exists(
            "Biological Asset Valuation", self.biological_asset_valuation
        ):
            valuation = frappe.get_doc("Biological Asset Valuation", self.biological_asset_valuation)
            if valuation.docstatus == 1:
                valuation.cancel()
        self.db_set("status", "Cancelled", update_modified=False)
