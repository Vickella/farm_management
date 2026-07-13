import frappe
from farm_management.permissions import apply_farm_permission_filter


def execute(filters=None):
    filters = filters or {}
    columns = [
        "Agreement:Link/Contract Farming Agreement:180",
        "Farmer:Link/Outgrower Farmer:180",
        "Farm:Link/Farm:150",
        "Status::100",
        "Crop:Link/Crop Type:140",
        "Production Target:Float:130",
        "Unit:Link/UOM:90",
        "Expected Purchase:Currency:150",
        "Inputs Disbursed:Currency:150",
        "Harvest Recovery:Currency:150",
        "Net Contract Position:Currency:160",
    ]
    return columns, get_data(filters)


def get_data(filters):
    conditions = []
    values = {}
    if not apply_farm_permission_filter(
        conditions, values, requested_farm=filters.get("farm")
    ):
        return []
    if filters.get("farmer"):
        conditions.append("farmer = %(farmer)s")
        values["farmer"] = filters.get("farmer")
    if filters.get("status"):
        conditions.append("status = %(status)s")
        values["status"] = filters.get("status")
    where = "where " + " and ".join(conditions) if conditions else ""

    return frappe.db.sql(
        f"""
        select
            name,
            farmer,
            farm,
            status,
            crop_type,
            production_target,
            unit,
            total_expected_purchase,
            actual_inputs_disbursed,
            harvest_recovery_value,
            net_contract_position
        from `tabContract Farming Agreement`
        {where}
        order by farm, farmer, name
        """,
        values,
    )
