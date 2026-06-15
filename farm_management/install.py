import frappe


def after_install():
    create_default_accounts()
    setup_farm_management_settings()
    print("farm_management installed successfully.")


def create_default_accounts():
    return None


def setup_farm_management_settings():
    if not frappe.db.exists("Farm Management Settings", "Farm Management Settings"):
        settings = frappe.new_doc("Farm Management Settings")
        settings.enable_ai_assistant = 1
        settings.enable_auto_activity_generation = 1
        settings.enable_fair_value_scheduler = 1
        settings.insert(ignore_permissions=True)
