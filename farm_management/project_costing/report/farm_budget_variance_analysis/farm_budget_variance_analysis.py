import frappe
from frappe.utils import flt
from farm_management.permissions import apply_farm_permission_filter


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
    if not apply_farm_permission_filter(
        conditions,
        values,
        sql_field="fb.farm",
        requested_farm=filters.get("farm"),
    ):
        return []
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
            case
                when ifnull(fbi.item, '') != '' then (
                    select coalesce(sum(pii.base_net_amount), 0)
                    from `tabPurchase Invoice Item` pii
                    inner join `tabPurchase Invoice` pi on pi.name = pii.parent
                    where pi.docstatus = 1
                      and pii.project = fb.project
                      and pii.item_code = fbi.item
                      and pi.posting_date between fb.budget_period_start and fb.budget_period_end
                )
                when ifnull(fbi.expense_account, '') != '' then (
                    select coalesce(sum(gl.debit - gl.credit), 0)
                    from `tabGL Entry` gl
                    where gl.is_cancelled = 0
                      and gl.project = fb.project
                      and gl.account = fbi.expense_account
                      and gl.posting_date between fb.budget_period_start and fb.budget_period_end
                )
                else 0
            end as actual_amount
        from `tabFarm Budget` fb
        inner join `tabFarm Budget Item` fbi on fbi.parent = fb.name
        {where}
        order by fb.farm, fb.project, fbi.idx
        """,
        values,
    )
    data = []
    for farm, project, category, description, budgeted, actual in rows:
        budgeted = flt(budgeted)
        actual = flt(actual)
        variance = actual - budgeted
        variance_percent = flt(variance / budgeted * 100, 2) if budgeted else 0
        variance_type = "Adverse" if variance > 0 else "Favourable"
        data.append(
            [
                farm,
                project,
                category,
                description,
                budgeted,
                actual,
                variance,
                variance_percent,
                variance_type,
            ]
        )
    return data
