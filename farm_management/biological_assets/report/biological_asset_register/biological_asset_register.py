import frappe


def execute(filters=None):
    filters = filters or {}
    columns = [
        "Biological Asset:Link/Biological Asset:160",
        "Asset Name::180",
        "Farm:Link/Farm:150",
        "Farm Type:Link/Farm Type:150",
        "Managed Item::150",
        "Status::100",
        "Quantity:Float:100",
        "Unit::90",
        "Initial Cost:Currency:130",
        "Capitalized Cost:Currency:140",
        "Current Fair Value:Currency:150",
        "Cost to Sell:Currency:120",
        "Net Fair Value:Currency:140",
        "Last Valuation Date:Date:130",
        "Last Journal Entry:Link/Journal Entry:160",
    ]
    return columns, get_data(filters)


def get_data(filters):
    conditions = []
    values = {}
    if filters.get("farm"):
        conditions.append("farm = %(farm)s")
        values["farm"] = filters.get("farm")
    if filters.get("farm_type"):
        conditions.append("farm_type = %(farm_type)s")
        values["farm_type"] = filters.get("farm_type")
    if filters.get("status"):
        conditions.append("status = %(status)s")
        values["status"] = filters.get("status")

    where = "where " + " and ".join(conditions) if conditions else ""
    return frappe.db.sql(
        f"""
        select
            name,
            asset_name,
            farm,
            farm_type,
            managed_item,
            status,
            quantity,
            unit,
            initial_cost,
            capitalized_cost,
            current_fair_value,
            cost_to_sell,
            net_fair_value,
            last_valuation_date,
            last_journal_entry
        from `tabBiological Asset`
        {where}
        order by farm, farm_type, managed_item, name
        """,
        values,
    )
