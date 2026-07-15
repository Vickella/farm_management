import frappe

def execute():
    ws = frappe.db.get_list("Workspace", filters={"name": "Farm Management"}, fields=["name", "is_standard", "public"])
    print(f"WORKSPACES: {ws}")

    # Check if there is any custom workspace
    custom = frappe.db.get_list("Workspace", filters={"extends_another_page": 1, "extends": "Farm Management"}, fields=["name"])
    print(f"CUSTOM EXTENSIONS: {custom}")

    # Let's also print the JSON content of the DB record
    doc = frappe.get_doc("Workspace", "Farm Management")
    print(f"DB CONTENT FIELD LENGTH: {len(doc.content or '')}")
    if doc.is_standard == 0:
        print("This is a custom workspace! Frappe is ignoring the JSON file!")
        # Delete it to restore standard
        frappe.delete_doc("Workspace", "Farm Management", force=1)
        print("Deleted custom workspace! Will be recreated from JSON on next migrate.")
        frappe.db.commit()
    
    if "farm-shortcuts-header" in (doc.content or ""):
        print("Wait, the DB still has the old layout content we removed from the JSON!")
        # The JSON was synced, but the DB still has old 'content'. Let's clear the content field!
        if doc.is_standard == 1:
            frappe.db.set_value("Workspace", "Farm Management", "content", None)
            frappe.db.commit()
            print("Cleared the content field directly in the DB! The UI should now fallback to the links array.")

