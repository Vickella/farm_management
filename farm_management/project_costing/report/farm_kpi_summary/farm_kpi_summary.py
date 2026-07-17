import frappe
from frappe.utils import flt, get_first_day, getdate, nowdate


def execute(filters=None):
    columns = [
        "Farm:Link/Farm:160",
        "Active Projects:Int:120",
        "Total Biological Asset Value:Currency:180",
        "Budget Utilisation %:Float:160",
        "Incidents This Month:Int:150",
    ]
    return columns, get_data()


def get_data():
    month_start = get_first_day(getdate(nowdate()))
    farms = frappe.get_list("Farm", pluck="name")
    projects = get_grouped_values(
        """
        select farm, count(*) as value
        from `tabProject`
        where ifnull(farm, '') != '' and status not in ('Completed', 'Cancelled')
        group by farm
        """
    )
    assets = get_grouped_values(
        """
        select farm, coalesce(sum(net_fair_value), 0) as value
        from `tabBiological Asset`
        where status = 'Active'
        group by farm
        """
    )
    budgets = get_grouped_values(
        """
        select farm, coalesce(sum(total_budget), 0) as value
        from `tabFarm Budget`
        where status in ('Approved', 'Active')
        group by farm
        """
    )
    actuals = get_grouped_values(
        """
        select farm, sum(value) as value
        from (
            select fb.farm, coalesce(sum(gl.debit - gl.credit), 0) as value
            from `tabFarm Budget` fb
            inner join `tabFarm Budget Item` fbi
                on fbi.parent = fb.name and ifnull(fbi.expense_account, '') != ''
            inner join `tabGL Entry` gl
                on gl.project = fb.project
                and gl.account = fbi.expense_account
                and gl.is_cancelled = 0
                and gl.posting_date between fb.budget_period_start and fb.budget_period_end
            where fb.status in ('Approved', 'Active')
            group by fb.name
            union all
            select fb.farm, coalesce(sum(pii.base_net_amount), 0) as value
            from `tabFarm Budget` fb
            inner join `tabFarm Budget Item` fbi
                on fbi.parent = fb.name and ifnull(fbi.item, '') != ''
            inner join `tabPurchase Invoice Item` pii
                on pii.project = fb.project and pii.item_code = fbi.item
            inner join `tabPurchase Invoice` pi
                on pi.name = pii.parent
                and pi.docstatus = 1
                and pi.posting_date between fb.budget_period_start and fb.budget_period_end
            where fb.status in ('Approved', 'Active')
            group by fb.name
        ) actual
        group by farm
        """
    )
    incidents = get_grouped_values(
        """
        select farm, count(*) as value
        from `tabDisease Incident`
        where incident_date >= %(month_start)s
        group by farm
        """,
        {"month_start": month_start},
    )
    rows = []
    for farm in farms:
        budget = flt(budgets.get(farm))
        utilisation = flt(flt(actuals.get(farm)) / budget * 100, 2) if budget else 0
        rows.append(
            [
                farm,
                projects.get(farm, 0),
                assets.get(farm, 0),
                utilisation,
                incidents.get(farm, 0),
            ]
        )
    return rows


def get_grouped_values(query, values=None):
    return {
        row.farm: row.value
        for row in frappe.db.sql(query, values or {}, as_dict=True)
        if row.farm
    }
