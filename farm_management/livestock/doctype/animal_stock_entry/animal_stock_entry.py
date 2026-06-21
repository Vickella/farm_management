import frappe
from frappe.model.document import Document
from frappe.utils import flt, today

from farm_management.biological_assets.valuation import (
    create_asset_outflow_journal_entry,
    create_asset_sale_proceeds_journal_entry,
    create_capitalization_document,
    reduce_asset_quantity,
    restore_asset_quantity,
)


class AnimalStockEntry(Document):
    def validate(self):
        if not self.posting_date:
            self.posting_date = today()
        if flt(self.quantity) <= 0:
            frappe.throw("Quantity must be greater than zero.")

        self.amount = flt(self.quantity) * flt(self.rate)
        self.validate_biological_asset()

    def validate_biological_asset(self):
        if not self.biological_asset:
            return

        asset = frappe.get_doc("Biological Asset", self.biological_asset)
        if self.farm and asset.farm != self.farm:
            frappe.throw("Animal Stock Entry farm must match the selected Biological Asset farm.")
        if not self.project and asset.linked_project:
            self.project = asset.linked_project
        if not self.unit:
            self.unit = asset.unit

        if self.species:
            species = frappe.get_doc("Livestock Species", self.species)
            if asset.managed_item and species.species_name != asset.managed_item:
                frappe.throw("Animal must match the managed item on the selected Biological Asset.")

        if self.breed and self.species:
            breed_species = frappe.db.get_value("Livestock Breed", self.breed, "species")
            if breed_species and breed_species != self.species:
                frappe.throw("Breed must belong to the selected Animal.")

    def on_submit(self):
        if self.entry_type in ("Opening", "Receipt", "Purchase", "Birth", "Transfer In", "Adjustment Increase"):
            self.apply_increase()
        elif self.entry_type in ("Issue", "Sale", "Death", "Transfer Out", "Adjustment Decrease"):
            self.apply_decrease()
        elif self.entry_type == "Cost Capitalization":
            self.apply_cost_capitalization()

        self.db_set("status", "Submitted", update_modified=False)

    def on_cancel(self):
        if self.capitalization and frappe.db.exists("Biological Asset Capitalization", self.capitalization):
            capitalization = frappe.get_doc("Biological Asset Capitalization", self.capitalization)
            if capitalization.docstatus == 1:
                capitalization.cancel()

        if flt(self.asset_value_reduction):
            restore_asset_quantity(
                self.biological_asset,
                self.quantity,
                self.asset_value_reduction,
                self.doctype,
                self.name,
            )

        if self.journal_entry and frappe.db.exists("Journal Entry", self.journal_entry):
            journal_entry = frappe.get_doc("Journal Entry", self.journal_entry)
            if journal_entry.docstatus == 1:
                journal_entry.cancel()

        if self.sale_journal_entry and frappe.db.exists("Journal Entry", self.sale_journal_entry):
            sale_journal_entry = frappe.get_doc("Journal Entry", self.sale_journal_entry)
            if sale_journal_entry.docstatus == 1:
                sale_journal_entry.cancel()

        self.db_set("status", "Cancelled", update_modified=False)

    def apply_increase(self):
        capitalization = create_capitalization_document(
            biological_asset=self.biological_asset,
            amount=self.amount,
            capitalization_type=get_capitalization_type(self.entry_type),
            source_doctype=self.doctype,
            source_name=self.name,
            remarks=f"Animal stock {self.entry_type}",
            quantity_delta=self.quantity,
            project=self.project,
        )
        if capitalization:
            self.db_set("capitalization", capitalization, update_modified=False)

    def apply_decrease(self):
        value_reduction = reduce_asset_quantity(
            self.biological_asset,
            self.quantity,
            self.doctype,
            self.name,
            empty_status=get_empty_asset_status(self.entry_type),
        )
        self.db_set("asset_value_reduction", value_reduction, update_modified=False)
        journal_entry = create_asset_outflow_journal_entry(
            self.biological_asset,
            value_reduction,
            posting_date=self.posting_date,
            project=self.project,
            source_doctype=self.doctype,
            source_name=self.name,
            remarks=f"Animal stock {self.entry_type}: {self.name}",
        )
        if journal_entry:
            self.db_set("journal_entry", journal_entry, update_modified=False)

        if self.entry_type == "Sale" and flt(self.sale_amount):
            sale_journal_entry = create_asset_sale_proceeds_journal_entry(
                self.biological_asset,
                self.sale_amount,
                posting_date=self.posting_date,
                project=self.project,
                source_doctype=self.doctype,
                source_name=self.name,
            )
            if sale_journal_entry:
                self.db_set("sale_journal_entry", sale_journal_entry, update_modified=False)

    def apply_cost_capitalization(self):
        capitalization = create_capitalization_document(
            biological_asset=self.biological_asset,
            amount=self.amount,
            capitalization_type="Other",
            source_doctype=self.doctype,
            source_name=self.name,
            remarks=f"Animal stock cost capitalization: {self.item or ''}",
            quantity_delta=0,
            project=self.project,
        )
        if capitalization:
            self.db_set("capitalization", capitalization, update_modified=False)


def get_capitalization_type(entry_type):
    if entry_type == "Birth":
        return "Birth"
    return "Purchase"


def get_empty_asset_status(entry_type):
    if entry_type == "Sale":
        return "Sold"
    if entry_type == "Death":
        return "Dead Loss"
    return "Harvested"
