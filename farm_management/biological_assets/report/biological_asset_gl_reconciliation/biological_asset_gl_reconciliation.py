import frappe

from farm_management.biological_assets.valuation import get_biological_asset_gl_reconciliation


def execute(filters=None):
    filters = frappe._dict(filters or {})
    columns = [
        {"fieldname": "account", "label": "Biological Asset Account", "fieldtype": "Link", "options": "Account", "width": 260},
        {"fieldname": "subledger_value", "label": "IAS 41 Subledger", "fieldtype": "Currency", "width": 150},
        {"fieldname": "gl_balance", "label": "GL Balance", "fieldtype": "Currency", "width": 150},
        {"fieldname": "difference", "label": "Difference", "fieldtype": "Currency", "width": 140},
        {"fieldname": "status", "label": "Status", "fieldtype": "Data", "width": 110},
    ]
    data = get_biological_asset_gl_reconciliation(
        company=filters.get("company"),
    )
    return columns, data
