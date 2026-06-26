import frappe
frappe.init(site='test.local')
frappe.connect()
if frappe.db.exists("Workspace", "Farm Management"):
    frappe.delete_doc("Workspace", "Farm Management", force=1)
    frappe.db.commit()
    print("Deleted Workspace")
