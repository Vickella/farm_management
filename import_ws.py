import frappe
from frappe.modules.import_file import import_file_by_path

frappe.init(site='test.local')
frappe.connect()

path = '/home/frappe/frappe-bench/apps/farm_management/farm_management/farm_setup/workspace/farm_management/farm_management.json'
import_file_by_path(path, force=True, data_import=False)
frappe.db.commit()
print("Imported JSON successfully!")
