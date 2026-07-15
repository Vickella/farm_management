import frappe

def execute():
    try:
        frappe.db.delete("Workspace", "Farm Management")
        frappe.db.commit()
        print("Deleted Workspace from DB")
    except Exception as e:
        print(f"Delete failed: {e}")
