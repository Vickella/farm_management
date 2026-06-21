import frappe
from frappe.model.document import Document
from frappe.utils import flt
from farm_management.biological_assets.valuation import create_capitalization_document


class LivestockHealthEvent(Document):
    def validate(self):
        self.fetch_item_cost()
        if self.weight_kg and self.animal:
            frappe.db.set_value(
                "Livestock Individual",
                self.animal,
                "current_weight_kg",
                self.weight_kg,
                update_modified=False,
            )

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
            capitalization_type="Health Cost",
            source_doctype=self.doctype,
            source_name=self.name,
            remarks=f"Capitalised livestock health event: {self.event_type}",
        )
        self.db_set("biological_asset", biological_asset, update_modified=False)
        if capitalization:
            self.db_set("capitalization", capitalization, update_modified=False)
        self.db_set("capitalized_to_asset", 1, update_modified=False)
