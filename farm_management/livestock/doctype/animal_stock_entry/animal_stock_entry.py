import frappe
from frappe.model.document import Document
from frappe.utils import flt, today

from farm_management.biological_assets.valuation import (
    create_asset_outflow_journal_entry,
    create_capitalization_document,
    get_biological_asset_account,
    get_biological_asset_cost_of_sales_account,
    get_company,
    get_asset_valuation_snapshot,
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
        self.validate_standard_invoice()

    def validate_standard_invoice(self):
        if self.entry_type not in ("Purchase", "Sale"):
            return
        if not self.item:
            frappe.throw("Item is required for a live-animal purchase or sale.")

        invoice_doctype = "Purchase Invoice" if self.entry_type == "Purchase" else "Sales Invoice"
        invoice_field = "purchase_invoice" if self.entry_type == "Purchase" else "sales_invoice"
        invoice_name = self.get(invoice_field)
        if not invoice_name:
            frappe.throw(f"A submitted {invoice_doctype} is required for {self.entry_type}.")
        invoice = frappe.get_doc(invoice_doctype, invoice_name)
        if invoice.docstatus != 1 or invoice.get("is_return"):
            frappe.throw(f"{invoice_doctype} {invoice.name} must be submitted and must not be a return.")

        asset = frappe.get_doc("Biological Asset", self.biological_asset)
        company = get_company(asset)
        if invoice.company != company:
            frappe.throw(f"{invoice_doctype} company must be {company}.")
        if frappe.db.get_value("Item", self.item, "is_stock_item"):
            frappe.throw("The invoice Item for a live Biological Asset must be a non-stock Item.")

        rows = [row for row in invoice.get("items", []) if row.item_code == self.item]
        if self.project:
            rows = [row for row in rows if row.project == self.project]
        if not rows:
            frappe.throw(f"{invoice_doctype} {invoice.name} has no matching Item and Project row.")
        if any(row.uom != self.unit for row in rows):
            frappe.throw(f"All matching {invoice_doctype} rows must use UOM {self.unit}.")

        duplicate_filters = {
            invoice_field: invoice.name,
            "item": self.item,
            "docstatus": 1,
            "name": ["!=", self.name or ""],
        }
        if frappe.db.exists("Animal Stock Entry", duplicate_filters):
            frappe.throw(f"{invoice_doctype} {invoice.name} and Item {self.item} are already linked to another entry.")

        invoiced_quantity = sum(flt(row.qty) for row in rows)
        invoiced_amount = sum(flt(row.base_net_amount) for row in rows)
        if invoiced_quantity <= 0 or invoiced_amount < 0:
            frappe.throw(f"{invoice_doctype} must contain a positive quantity and non-negative base amount.")

        self.posting_date = invoice.posting_date
        self.quantity = invoiced_quantity
        if self.entry_type == "Purchase":
            expense_accounts = {row.expense_account for row in rows}
            if len(expense_accounts) != 1 or not next(iter(expense_accounts), None):
                frappe.throw(
                    "All matching Purchase Invoice rows must use the same Expense Head so the exact "
                    "amount can be transferred into the Biological Asset account."
                )
            self.purchase_expense_account = next(iter(expense_accounts))
            self.supplier = invoice.supplier
            self.amount = invoiced_amount
            self.rate = invoiced_amount / invoiced_quantity
        else:
            self.customer = invoice.customer
            self.sale_amount = invoiced_amount
            self.amount = flt(self.rate) * invoiced_quantity

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

        if not self.species and asset.managed_item:
            self.species = frappe.db.get_value(
                "Livestock Species", {"species_name": asset.managed_item, "is_active": 1}, "name"
            )
        if not self.breed and asset.livestock_breed:
            self.breed = asset.livestock_breed
        if not self.rate and self.entry_type in ("Issue", "Sale", "Death", "Transfer") and flt(asset.quantity):
            self.rate = flt(asset.net_fair_value) / flt(asset.quantity)
            self.amount = flt(self.quantity) * flt(self.rate)

        if self.species:
            species = frappe.get_doc("Livestock Species", self.species)
            if asset.managed_item and species.species_name != asset.managed_item:
                frappe.throw("Animal must match the managed item on the selected Biological Asset.")

        if self.breed and self.species:
            breed_species = frappe.db.get_value("Livestock Breed", self.breed, "species")
            if breed_species and breed_species != self.species:
                frappe.throw("Breed must belong to the selected Animal.")

    def on_submit(self):
        if self.entry_type in ("Opening", "Receipt", "Purchase", "Birth"):
            self.apply_increase()
        elif self.entry_type in ("Issue", "Sale", "Death"):
            self.apply_decrease()
        elif self.entry_type == "Transfer":
            self.apply_transfer()

        self.db_set("status", "Submitted", update_modified=False)

    def on_cancel(self):
        if self.journal_entry and frappe.db.exists("Journal Entry", self.journal_entry):
            journal_entry = frappe.get_doc("Journal Entry", self.journal_entry)
            if journal_entry.docstatus == 1:
                journal_entry.cancel()

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
                valuation_snapshot=self.valuation_snapshot,
            )

        if self.entry_type == "Transfer" and self.target_farm:
            asset = frappe.get_doc("Biological Asset", self.biological_asset)
            asset.db_set("farm", self.farm)

        self.db_set("status", "Cancelled", update_modified=False)

    def apply_increase(self):
        capitalization = create_capitalization_document(
            biological_asset=self.biological_asset,
            amount=self.amount,
            posting_date=self.posting_date,
            capitalization_type=get_capitalization_type(self.entry_type),
            source_doctype=self.doctype,
            source_name=self.name,
            remarks=f"Animal stock {self.entry_type}",
            quantity_delta=self.quantity,
            project=self.project,
            post_gl_entry=True,
            credit_account=self.purchase_expense_account if self.entry_type == "Purchase" else None,
            accounting_source_doctype="Purchase Invoice" if self.entry_type == "Purchase" else None,
            accounting_source_name=self.purchase_invoice if self.entry_type == "Purchase" else None,
        )
        if capitalization:
            self.db_set("capitalization", capitalization, update_modified=False)

    def apply_decrease(self):
        self.db_set(
            "valuation_snapshot",
            get_asset_valuation_snapshot(self.biological_asset),
            update_modified=False,
        )
        value_reduction = reduce_asset_quantity(
            self.biological_asset,
            self.quantity,
            self.doctype,
            self.name,
            empty_status=get_empty_asset_status(self.entry_type),
        )
        self.db_set("asset_value_reduction", value_reduction, update_modified=False)
        debit_account = None
        if self.entry_type == "Sale":
            debit_account = get_biological_asset_cost_of_sales_account(self.biological_asset)
            if not debit_account:
                frappe.throw("Configure the Biological Asset Cost of Sales account before selling live animals.")
        journal_entry = create_asset_outflow_journal_entry(
            self.biological_asset,
            value_reduction,
            posting_date=self.posting_date,
            project=self.project,
            source_doctype=self.doctype,
            source_name=self.name,
            remarks=f"Carrying value derecognition for animal {self.entry_type}",
            debit_account=debit_account,
        )
        if journal_entry:
            self.db_set("journal_entry", journal_entry, update_modified=False)

    def apply_transfer(self):
        if not self.target_farm:
            frappe.throw("Target Farm is required for Transfer.")
        if self.target_farm == self.farm:
            frappe.throw("Target Farm must be different from the source Farm.")
        asset = frappe.get_doc("Biological Asset", self.biological_asset)
        if flt(self.quantity) < flt(asset.quantity):
            frappe.throw("Partial transfer of biological asset is not supported via Stock Entry. Please split the asset first.")
        asset.db_set("farm", self.target_farm)


def get_capitalization_type(entry_type):
    if entry_type in ("Opening", "Receipt", "Purchase", "Birth"):
        return entry_type
    return "Other"


def get_empty_asset_status(entry_type):
    if entry_type == "Sale":
        return "Sold"
    if entry_type == "Death":
        return "Dead Loss"
    return "Harvested"
