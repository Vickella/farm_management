import frappe
from frappe.model.document import Document

class BroilerBatch(Document):
	def on_submit(self):
		# Automatically create a Biological Asset Valuation when a batch is submitted/updated
		val = frappe.new_doc("Biological Asset Valuation")
		val.date = self.date
		val.farm = self.farm
		val.project = self.project
		val.asset_category = "Poultry"
		val.valuation_type = "Growth"
		val.remarks = f"Automatic valuation from Broiler Batch: {self.name}"
		# In a real scenario, this would compute based on bird weight, mortality, and market prices.
		val.insert(ignore_permissions=True)
		val.submit()
		frappe.msgprint(f"Biological Asset Valuation {val.name} generated for {self.name}.")
