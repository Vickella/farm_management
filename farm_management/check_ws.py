import frappe
import json

def execute():
    try:
        ws = frappe.get_doc("Workspace", "Farm Management")
        print("Workspace found in DB.")
        print("Content length:", len(ws.content))
        if "Poultry Production" in ws.content:
            print("SUCCESS: The new layout is in the database.")
        else:
            print("FAIL: The old layout is in the database.")
    except Exception as e:
        print("Workspace NOT found in DB:", e)

    # Let's forcefully sync it now just in case
    print("Force syncing workspace...")
    from frappe.modules.import_file import import_file_by_path
    path = '/home/frappe/frappe-bench/apps/farm_management/farm_management/farm_setup/workspace/farm_management/farm_management.json'
    import_file_by_path(path, force=True, data_import=False)
    frappe.db.commit()
    print("Done importing.")
    
    ws = frappe.get_doc("Workspace", "Farm Management")
    if "Poultry Production" in ws.content:
        print("POST-SYNC SUCCESS: The new layout is in the database.")
    else:
        print("POST-SYNC FAIL: The old layout is STILL in the database.")
