import frappe
from frappe.model.document import Document
from frappe.utils import flt
from farm_management.server_validation import apply_project_context, validate_asset_context, validate_date_order


class HarvestLog(Document):
    def validate(self):
        self.set_project_defaults()
        self.set_item_defaults()
        self.harvest_completion = self.harvest_completion or "Final"
        if not self.title:
            self.title = f"{self.project} Harvest - {self.date}"
        if flt(self.harvested_quantity) <= 0:
            frappe.throw("Harvested Quantity must be greater than zero.")
        if flt(self.harvest_fair_value) <= 0:
            frappe.throw("Harvest Fair Value must be greater than zero.")
        if self.harvest_completion == "Partial":
            if flt(self.remaining_crop_fair_value) <= 0:
                frappe.throw(
                    "Remaining Crop Fair Value must be greater than zero for a partial harvest. "
                    "Choose Final when the crop asset is fully harvested."
                )
        else:
            self.harvest_completion = "Final"
            self.remaining_crop_fair_value = 0
        if self.moisture_content is not None and not 0 <= flt(self.moisture_content) <= 100:
            frappe.throw("Moisture Content must be between 0 and 100 percent.")
        self.valuation_rate = flt(self.harvest_fair_value) / flt(
            self.harvested_quantity
        )
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
        output_item = frappe.db.get_value(
            "Biological Asset", self.biological_asset, "output_item"
        )
        if not output_item:
            frappe.throw(
                "The Biological Asset has no Expected Output Item. Configure it before harvesting."
            )
        self.conversion_item = output_item
        self.harvest_uom = frappe.db.get_value("Item", output_item, "stock_uom")
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
                "final_harvest": 1 if self.harvest_completion == "Final" else 0,
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
        target_net_fair_value = flt(self.harvest_fair_value) + (
            flt(self.remaining_crop_fair_value)
            if self.harvest_completion == "Partial"
            else 0
        )
        if abs(flt(asset.net_fair_value) - target_net_fair_value) <= 0.01:
            return
        later_valuation = frappe.db.get_value(
            "Biological Asset Valuation",
            {
                "biological_asset": asset.name,
                "valuation_date": [">", self.date],
                "docstatus": 1,
            },
            "name",
            order_by="valuation_date desc",
        )
        if later_valuation:
            frappe.throw(
                f"Cancel later Biological Asset Valuation {later_valuation} before posting this harvest."
            )
        same_day_valuation = frappe.db.get_value(
            "Biological Asset Valuation",
            {
                "biological_asset": asset.name,
                "valuation_date": self.date,
                "docstatus": ["<", 2],
            },
            ["name", "docstatus", "net_fair_value"],
            as_dict=True,
        )
        if same_day_valuation:
            frappe.throw(
                f"Biological Asset Valuation {same_day_valuation.name} already exists on the harvest date. "
                f"Set its Net Fair Value to {target_net_fair_value} and submit it before retrying."
            )
        valuation = frappe.get_doc(
            {
                "doctype": "Biological Asset Valuation",
                "biological_asset": asset.name,
                "valuation_date": self.date,
                "valuation_method": "Manual Fair Value",
                "current_fair_value": target_net_fair_value,
                "cost_to_sell": 0,
                "valuation_basis": (
                    f"Fair value at harvest from Harvest Log {self.name}; "
                    f"{self.harvest_completion.lower()} harvest"
                ),
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
                transaction.flags.ignore_permissions = True
                transaction.cancel()
        if self.biological_asset_valuation and frappe.db.exists(
            "Biological Asset Valuation", self.biological_asset_valuation
        ):
            valuation = frappe.get_doc("Biological Asset Valuation", self.biological_asset_valuation)
            if valuation.docstatus == 1:
                valuation.flags.ignore_permissions = True
                valuation.cancel()
        self.db_set("status", "Cancelled", update_modified=False)
