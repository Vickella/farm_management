import frappe


INCREASE_TYPES = ("Opening", "Receipt", "Purchase", "Birth", "Transfer In", "Adjustment Increase")
DECREASE_TYPES = ("Issue", "Sale", "Death", "Transfer Out", "Adjustment Decrease")


def execute(filters=None):
    filters = filters or {}
    columns = [
        "Posting Date:Date:110",
        "Animal Stock Entry:Link/Animal Stock Entry:170",
        "Entry Type::140",
        "Farm:Link/Farm:150",
        "Biological Asset:Link/Biological Asset:160",
        "Animal:Link/Livestock Species:140",
        "Breed:Link/Livestock Breed:140",
        "In Qty:Float:90",
        "Out Qty:Float:90",
        "Unit::80",
        "Unit Cost / Rate:Currency:130",
        "Amount:Currency:120",
        "Asset Value Reduction:Currency:160",
        "Capitalization:Link/Biological Asset Capitalization:160",
        "Journal Entry:Link/Journal Entry:160",
    ]
    return columns, get_data(filters)


def get_data(filters):
    conditions = ["docstatus = 1"]
    values = {}
    if filters.get("farm"):
        conditions.append("farm = %(farm)s")
        values["farm"] = filters.get("farm")
    if filters.get("biological_asset"):
        conditions.append("biological_asset = %(biological_asset)s")
        values["biological_asset"] = filters.get("biological_asset")
    if filters.get("from_date"):
        conditions.append("posting_date >= %(from_date)s")
        values["from_date"] = filters.get("from_date")
    if filters.get("to_date"):
        conditions.append("posting_date <= %(to_date)s")
        values["to_date"] = filters.get("to_date")

    rows = frappe.db.sql(
        f"""
        select
            posting_date,
            name,
            entry_type,
            farm,
            biological_asset,
            species,
            breed,
            quantity,
            unit,
            rate,
            amount,
            asset_value_reduction,
            capitalization,
            journal_entry
        from `tabAnimal Stock Entry`
        where {" and ".join(conditions)}
        order by posting_date, creation, name
        """,
        values,
        as_dict=True,
    )

    data = []
    for row in rows:
        in_qty = row.quantity if row.entry_type in INCREASE_TYPES else 0
        out_qty = row.quantity if row.entry_type in DECREASE_TYPES else 0
        data.append(
            [
                row.posting_date,
                row.name,
                row.entry_type,
                row.farm,
                row.biological_asset,
                row.species,
                row.breed,
                in_qty,
                out_qty,
                row.unit,
                row.rate,
                row.amount,
                row.asset_value_reduction,
                row.capitalization,
                row.journal_entry,
            ]
        )
    return data
