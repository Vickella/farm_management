import frappe
from frappe.utils import flt, get_first_day, getdate, nowdate


def execute(filters=None):
    columns = [
        "Farm:Link/Farm:160",
        "Active Projects:Int:120",
        "Total Biological Asset Value:Currency:180",
        "Budget Utilisation %:Float:160",
        "Incidents This Month:Int:150",
        "Contracts Active:Int:130",
    ]
    return columns, get_data()


def get_data():
    month_start = get_first_day(getdate(nowdate()))
    rows = []
    for farm in frappe.get_all("Farm", pluck="name"):
        active_projects = frappe.db.count("Project", {"farm": farm, "status": ["not in", ["Completed", "Cancelled"]]})
        asset_value = frappe.db.sql(
            """
            select coalesce(sum(net_fair_value), 0)
            from `tabBiological Asset`
            where farm = %s and status = 'Active'
            """,
            farm,
        )[0][0]
        budget = frappe.db.sql(
            """
            select coalesce(sum(total_budget), 0), coalesce(sum(total_actual), 0)
            from `tabFarm Budget`
            where farm = %s and status in ('Approved', 'Active')
            """,
            farm,
        )[0]
        utilisation = flt((flt(budget[1]) / flt(budget[0])) * 100, 2) if flt(budget[0]) else 0
        incidents = frappe.db.count("Disease Incident", {"farm": farm, "incident_date": [">=", month_start]})
        contracts = frappe.db.count("Contract Farming Agreement", {"farm": farm, "status": "Active"})
        rows.append([farm, active_projects, asset_value, utilisation, incidents, contracts])
    return rows
