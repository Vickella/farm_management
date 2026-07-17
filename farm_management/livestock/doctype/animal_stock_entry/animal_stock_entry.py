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
from farm_management.server_validation import get_farm_context, validate_asset_context, validate_non_negative


class AnimalStockEntry(Document):
    def validate(self):
        if not self.posting_date:
            self.posting_date = today()
        if flt(self.quantity) <= 0:
            frappe.throw("Quantity must be greater than zero.")
        validate_non_negative(self, ("rate", "amount", "sale_amount"))

        self.set_project_defaults()
        self.validate_biological_asset()
        self.set_batch_reference()
        self.set_invoice_item_default()
        self.validate_standard_invoice()
        if self.entry_type in ("Opening", "Receipt", "Birth") and flt(self.rate) <= 0:
            frappe.throw(
                f"Unit Cost / Rate must be greater than zero for {self.entry_type}."
            )
        self.amount = flt(self.quantity) * flt(self.rate)

    def set_project_defaults(self):
        if not self.project:
            return
        project = frappe.db.get_value(
            "Project",
            self.project,
            [
                "farm",
                "biological_asset",
                "managed_item_doctype",
                "managed_crop_animal_species",
                "animal_breed",
                "project_unit",
            ],
            as_dict=True,
        )
        if not project or project.managed_item_doctype != "Livestock Species":
            frappe.throw(
                f"Project {self.project} is not configured as an animal or poultry "
                "Agriculture Project. Open the Project, select an Agriculture Project "
                "Type such as Pig Farming or Broiler Production, select its managed "
                "animal, Farm, quantity, and UOM, then save it."
            )
        if not project.biological_asset:
            from farm_management.farm_projects.agriculture_project import (
                sync_biological_asset_for_project,
            )

            project_doc = frappe.get_doc("Project", self.project)
            sync_biological_asset_for_project(project_doc)
            project.biological_asset = frappe.db.get_value(
                "Project", self.project, "biological_asset"
            )
        if not project.biological_asset:
            frappe.throw(
                f"Could not create the Biological Asset for Project {self.project}. "
                "Check its Farm Type, managed animal, output Item, and UOM."
            )
        if self.biological_asset and self.biological_asset != project.biological_asset:
            frappe.throw("Biological Asset must be the asset linked to the selected Project.")
        self.biological_asset = project.biological_asset
        self.farm = project.farm
        self.species = project.managed_crop_animal_species
        if not self.breed:
            self.breed = project.animal_breed
        if not self.unit:
            self.unit = project.project_unit

    def set_batch_reference(self):
        if self.entry_type in ("Opening", "Receipt", "Purchase", "Birth"):
            self.batch_reference = self.batch_reference or self.name

    def set_invoice_item_default(self):
        if self.entry_type not in ("Purchase", "Sale") or self.item:
            return
        invoice_doctype = (
            "Purchase Invoice" if self.entry_type == "Purchase" else "Sales Invoice"
        )
        invoice_field = (
            "purchase_invoice" if self.entry_type == "Purchase" else "sales_invoice"
        )
        invoice_name = self.get(invoice_field)
        if invoice_name:
            invoice = frappe.get_doc(invoice_doctype, invoice_name)
            candidate_rows = [
                row
                for row in invoice.get("items", [])
                if not self.project or row.project == self.project
            ]
            non_stock_items = {
                row.item_code
                for row in candidate_rows
                if row.item_code
                and not frappe.db.get_value("Item", row.item_code, "is_stock_item")
            }
            if len(non_stock_items) == 1:
                self.item = non_stock_items.pop()
                return
            if len(non_stock_items) > 1:
                frappe.throw(
                    f"{invoice_doctype} {invoice_name} has multiple non-stock Items for "
                    f"Project {self.project}. Keep one live-animal Item on the Project row."
                )
        if not self.species:
            frappe.throw("Animal is required before the live-animal invoice Item can be selected.")
        self.item = get_or_create_live_animal_invoice_item(self.species, self.unit)

    def validate_standard_invoice(self):
        if self.entry_type not in ("Purchase", "Sale"):
            return
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
        validate_asset_context(asset.name, active=True)
        if self.farm and asset.farm != self.farm:
            frappe.throw("Animal Stock Entry farm must match the selected Biological Asset farm.")
        self.farm = asset.farm
        get_farm_context(self.farm)
        if not self.project and asset.linked_project:
            self.project = asset.linked_project
        if not self.unit:
            self.unit = asset.unit
        if self.unit != asset.unit:
            frappe.throw(f"Movement Unit must match Biological Asset UOM {asset.unit}.")
        if self.entry_type in ("Issue", "Sale", "Death", "Transfer") and flt(self.quantity) > flt(asset.quantity):
            frappe.throw("Movement Quantity cannot exceed the Biological Asset quantity.")
        if self.entry_type == "Opening" and flt(asset.quantity) > 0:
            # A Project has only one opening balance. Later additions are receipts into
            # the same herd/flock asset, even when the user starts from the Opening action.
            self.entry_type = "Receipt"

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
            breed_species = frappe.db.get_value("Livestock Breed", {"name": self.breed, "is_active": 1}, "species")
            if not breed_species or breed_species != self.species:
                frappe.throw("Breed must belong to the selected Animal.")
        if self.livestock_individual:
            individual = frappe.db.get_value("Livestock Individual", self.livestock_individual, ["farm", "species", "breed", "biological_asset"], as_dict=True)
            if not individual:
                frappe.throw("Select a valid Livestock Individual.")
            if individual.farm != self.farm or individual.biological_asset != self.biological_asset:
                frappe.throw("Individual Animal must belong to the selected Farm and Biological Asset.")
            if self.species and individual.species != self.species:
                frappe.throw("Individual Animal species must match the movement species.")

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
                journal_entry.flags.ignore_permissions = True
                journal_entry.cancel()

        if self.capitalization and frappe.db.exists("Biological Asset Capitalization", self.capitalization):
            capitalization = frappe.get_doc("Biological Asset Capitalization", self.capitalization)
            if capitalization.docstatus == 1:
                capitalization.flags.ignore_permissions = True
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
        source = get_farm_context(self.farm)
        target = get_farm_context(self.target_farm)
        if source.owner_name != target.owner_name:
            frappe.throw("Transfers between different Companies require accounting documents and are not supported.")
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


def get_or_create_live_animal_invoice_item(species_name, stock_uom=None):
    """Return the deterministic non-stock invoice Item for a live animal species."""
    species = frappe.get_doc("Livestock Species", species_name)
    key = frappe.scrub(species.species_name or species.name).upper().replace("_", "-")
    item_code = f"LIVE-ANIMAL-{key}"
    existing = frappe.db.get_value(
        "Item", item_code, ["name", "disabled", "is_stock_item"], as_dict=True
    )
    if existing:
        if existing.disabled or existing.is_stock_item:
            frappe.throw(
                f"Automatic live-animal Item {item_code} must be enabled and non-stock."
            )
        return existing.name

    from farm_management.install import ensure_farm_produce_item_group

    item = frappe.new_doc("Item")
    item.item_code = item_code
    item.item_name = f"Live {species.species_name or species.name}"
    item.item_group = ensure_farm_produce_item_group()
    item.stock_uom = stock_uom or (
        "Bird" if species.species_group == "Poultry" else "Head"
    )
    item.is_stock_item = 0
    item.is_sales_item = 1
    item.is_purchase_item = 1
    item.disabled = 0
    item.description = (
        "Non-stock invoice Item for live biological-asset purchases and sales. "
        "Quantity and carrying value are controlled by Animal Stock Entry and IAS 41."
    )
    item.insert(ignore_permissions=True)
    return item.name
