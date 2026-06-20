import frappe
from frappe.utils import flt


def execute(filters=None):
    columns = [
        "Farm:Link/Farm:160",
        "Project:Link/Project:160",
        "Item Category::130",
        "Item Description::180",
        "Budgeted Amount:Currency:140",
        "Actual Amount:Currency:140",
        "Variance:Currency:120",
        "Variance %:Float:100",
        "Variance Type::100",
    ]
    return columns, get_data(filters or {})


def get_data(filters):
    conditions = []
    values = {}
    if filters.get("farm"):
        conditions.append("fb.farm = %(farm)s")
        values["farm"] = filters.get("farm")
    if filters.get("project"):
        conditions.append("fb.project = %(project)s")
        values["project"] = filters.get("project")
    where = "where " + " and ".join(conditions) if conditions else ""

    rows = frappe.db.sql(
        f"""
        select
            fb.farm,
            fb.project,
            fbi.item_category,
            fbi.item_description,
            fbi.budgeted_amount,
            fbi.actual_amount,
            fbi.variance,
            fbi.variance_percent,
            fbi.variance_type
        from `tabFarm Budget` fb
        inner join `tabFarm Budget Item` fbi on fbi.parent = fb.name
        {where}
        order by fb.farm, fb.project, fbi.idx
        """,
        values,
    )
    return [[*row[:6], flt(row[6]), flt(row[7]), row[8]] for row in rows]
