import frappe
from frappe.model.document import Document
from farm_management.biological_assets.valuation import reduce_asset_quantity


class HarvestTransaction(Document):
    def on_submit(self):
        reduce_asset_quantity(
            self.biological_asset,
            self.quantity_harvested,
            source_doctype=self.doctype,
            source_name=self.name,
        )
        if self.conversion_item and not self.stock_entry:
            se = frappe.new_doc("Stock Entry")
            se.stock_entry_type = "Material Receipt"
            se.posting_date = self.harvest_date
            se.append(
                "items",
                {
                    "item_code": self.conversion_item,
                    "qty": self.quantity_harvested,
                    "uom": self.unit,
                    "basic_rate": self.harvest_value or 0,
                },
            )
            se.insert(ignore_permissions=True)
            se.submit()
            self.db_set("stock_entry", se.name)
