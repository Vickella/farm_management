import frappe

def execute():
    if frappe.db.exists("Workspace", "Farm Management"):
        frappe.delete_doc("Workspace", "Farm Management", force=1)
        frappe.db.commit()
        print("Deleted existing Farm Management Workspace")
    else:
        print("Workspace not found")
