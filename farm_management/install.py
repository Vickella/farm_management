import frappe


def after_install():
    create_roles()
    create_farm_workspace()
    setup_farm_management_settings()
    frappe.db.commit()
    print("farm_management: installation complete.")


def create_roles():
    for role in ["Farm Manager", "Farm Worker", "Agronomist"]:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role}).insert(ignore_permissions=True)


def setup_farm_management_settings():
    if not frappe.db.exists("Farm Management Settings", "Farm Management Settings"):
        doc = frappe.new_doc("Farm Management Settings")
        doc.enable_ai_assistant = 1
        doc.enable_auto_activity_generation = 1
        doc.enable_fair_value_scheduler = 1
        doc.insert(ignore_permissions=True)


def create_farm_workspace():
    if frappe.db.exists("Workspace", "Farm Management"):
        return

    ws = frappe.new_doc("Workspace")
    ws.name = "Farm Management"
    ws.label = "Farm Management"
    ws.category = "Modules"
    ws.icon = "agriculture"
    ws.is_standard = 1
    ws.module = "Farm Setup"
    ws.public = 1

    shortcuts = ["Farm", "Farm Field", "Farm Pond", "Farm Pen", "Fowl Run", "Biological Asset", "Harvest Transaction", "Farm BOM", "Farm Budget", "Disease Incident", "Pest", "Animal Disease", "Farm Activity", "Outgrower Farmer", "Contract Farming Agreement", "Input Loan Disbursement", "Harvest Recovery", "Farm Management Settings"]
    for doctype in shortcuts:
        ws.append("shortcuts", {"label": doctype, "type": "DocType", "link_to": doctype})

    cards = [
        ("Farm Setup", ["Farm", "Farm Type", "Crop Type", "Farm Management Settings"]),
        ("Farm Infrastructure", ["Farm Field", "Farm Pond", "Farm Pen", "Fowl Run"]),
        ("Farm Projects & Calendar", ["Farm Activity", "Farm Activity Type"]),
        ("Biological Assets (IFRS 41)", ["Biological Asset", "Harvest Transaction"]),
        ("Disease & Pest Intelligence", ["Disease Incident", "Pest", "Animal Disease"]),
        ("Farm BOM & Budgeting", ["Farm BOM", "Farm Budget"]),
        ("Contract Farming", ["Outgrower Farmer", "Contract Farming Agreement", "Input Loan Disbursement", "Harvest Recovery"]),
        ("Reports", ["Farm KPI Summary", "Farm Budget Variance Analysis"]),
    ]
    for label, links in cards:
        ws.append("content", {"type": "Card Break", "label": label})
        for link in links:
            ws.append("content", {"type": "Link", "label": link, "link_type": "DocType", "link_to": link})
    ws.insert(ignore_permissions=True)
