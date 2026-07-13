import frappe
from frappe.model.document import Document
from frappe.utils import flt
from farm_management.biological_assets.valuation import (
    create_capitalization_document,
    get_capitalization_source_account,
)


class LivestockHealthEvent(Document):
    def validate(self):
        self.validate_capitalization_immutability()
        self.fetch_item_cost()
        self.validate_capitalization_source()
        if self.weight_kg and self.animal:
            frappe.db.set_value(
                "Livestock Individual",
                self.animal,
                "current_weight_kg",
                self.weight_kg,
                update_modified=False,
            )

    def validate_capitalization_source(self):
        if (
            not self.capitalize_cost
            or self.status != "Completed"
            or not flt(self.cost)
            or self.capitalized_to_asset
        ):
            return
        biological_asset = self.biological_asset or frappe.db.get_value(
            "Livestock Individual", self.animal, "biological_asset"
        )
        if not biological_asset:
            frappe.throw("The selected animal must be linked to a Biological Asset.")
        self.capitalization_credit_account = get_capitalization_source_account(
            biological_asset,
            self.capitalization_source_doctype,
            self.capitalization_source,
            self.cost,
        )

    def validate_capitalization_immutability(self):
        previous = self.get_doc_before_save()
        if not previous or not previous.capitalized_to_asset:
            return
        protected = (
            "status",
            "event_date",
            "cost",
            "biological_asset",
            "animal",
            "capitalization_source_doctype",
            "capitalization_source",
        )
        if any(previous.get(fieldname) != self.get(fieldname) for fieldname in protected):
            frappe.throw("Cancel the linked Biological Asset Capitalization before changing posted health costs.")

    def fetch_item_cost(self):
        if self.product_used and not flt(self.cost):
            self.cost = flt(frappe.db.get_value("Item", self.product_used, "valuation_rate"))

    def on_update(self):
        self.capitalize_health_cost()

    def capitalize_health_cost(self):
        if not self.capitalize_cost or self.capitalized_to_asset or self.status != "Completed":
            return

        biological_asset = self.biological_asset
        if not biological_asset and self.animal:
            biological_asset = frappe.db.get_value(
                "Livestock Individual",
                self.animal,
                "biological_asset",
            )

        if not biological_asset or not flt(self.cost):
            return

        capitalization = create_capitalization_document(
            biological_asset=biological_asset,
            amount=self.cost,
            posting_date=self.event_date,
            capitalization_type="Health Cost",
            source_doctype=self.doctype,
            source_name=self.name,
            remarks=f"Capitalised livestock health event: {self.event_type}",
            credit_account=self.capitalization_credit_account,
            accounting_source_doctype=self.capitalization_source_doctype,
            accounting_source_name=self.capitalization_source,
        )
        self.db_set("biological_asset", biological_asset, update_modified=False)
        if capitalization:
            self.db_set("capitalization", capitalization, update_modified=False)
        self.db_set("capitalized_to_asset", 1, update_modified=False)

    def on_trash(self):
        if self.capitalization and frappe.db.exists("Biological Asset Capitalization", self.capitalization):
            capitalization = frappe.get_doc("Biological Asset Capitalization", self.capitalization)
            if capitalization.docstatus == 1:
                capitalization.cancel()
