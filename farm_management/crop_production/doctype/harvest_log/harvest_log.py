import frappe
from frappe.model.document import Document

class HarvestLog(Document):
	def on_submit(self):
		val = frappe.new_doc("Biological Asset Valuation")
		val.date = self.date
		val.farm = self.farm
		val.project = self.project
		val.asset_category = "Crop Production"
		val.valuation_type = "Operation Update"
		val.remarks = f"Automatic valuation update from Harvest Log: {self.name}"
		val.insert(ignore_permissions=True)
		val.submit()
		frappe.msgprint(f"Biological Asset Valuation {val.name} generated for {self.name}.")
