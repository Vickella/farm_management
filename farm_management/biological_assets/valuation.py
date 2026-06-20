import frappe
from frappe.utils import flt, today


def capitalize_asset_cost(
    biological_asset,
    amount,
    source_doctype=None,
    source_name=None,
    remarks=None,
    quantity_delta=0,
    create_journal_entry=False,
):
    amount = flt(amount)
    quantity_delta = flt(quantity_delta)
    if not biological_asset or (not amount and not quantity_delta):
        return

    asset = frappe.get_doc("Biological Asset", biological_asset)

    if amount:
        asset.capitalized_cost = flt(asset.capitalized_cost) + amount

    if quantity_delta:
        asset.quantity = flt(asset.quantity) + quantity_delta

    asset.recalculate_valuation()
    asset.last_valuation_date = today()
    asset.add_comment(
        "Info",
        get_capitalization_comment(amount, source_doctype, source_name, remarks, quantity_delta),
    )
    asset.save(ignore_permissions=True)

    if create_journal_entry and amount:
        create_fair_value_journal_entry(asset)


def reduce_asset_quantity(biological_asset, quantity, source_doctype=None, source_name=None):
    quantity = flt(quantity)
    if not biological_asset or not quantity:
        return

    asset = frappe.get_doc("Biological Asset", biological_asset)
    if quantity > flt(asset.quantity):
        frappe.throw("Harvest quantity cannot exceed Biological Asset quantity.")

    asset.quantity = flt(asset.quantity) - quantity
    if flt(asset.quantity) <= 0:
        asset.quantity = 0
        asset.status = "Harvested"

    asset.recalculate_valuation(scale_by_quantity=True)
    asset.last_valuation_date = today()
    asset.add_comment(
        "Info",
        get_capitalization_comment(0, source_doctype, source_name, "Harvest quantity reduction", -quantity),
    )
    asset.save(ignore_permissions=True)


def sync_project_material_issue(stock_entry, method=None):
    if stock_entry.docstatus != 1 or stock_entry.stock_entry_type != "Material Issue":
        return

    project_totals = {}
    for item in stock_entry.get("items", []):
        project = item.get("project") or stock_entry.get("project")
        if not project:
            continue
        amount = flt(item.get("basic_amount")) or flt(item.get("amount"))
        if not amount:
            amount = flt(item.get("qty")) * flt(item.get("basic_rate"))
        project_totals[project] = project_totals.get(project, 0) + amount

    for project, amount in project_totals.items():
        asset_name = frappe.db.get_value(
            "Biological Asset",
            {"linked_project": project, "status": "Active"},
            "name",
        )
        if asset_name and amount:
            capitalize_asset_cost(
                asset_name,
                amount,
                source_doctype=stock_entry.doctype,
                source_name=stock_entry.name,
                remarks=f"Material Issue capitalised from Project {project}",
            )


def create_fair_value_journal_entry(asset):
    settings = frappe.get_single("Farm Management Settings")
    if not settings.biological_asset_account or not settings.fair_value_gain_loss_account:
        return

    company = get_company(asset)
    if not company:
        return

    delta = flt(asset.net_fair_value) - flt(asset.last_posted_net_fair_value)
    if not delta:
        return

    journal_entry = frappe.new_doc("Journal Entry")
    journal_entry.voucher_type = "Journal Entry"
    journal_entry.company = company
    journal_entry.posting_date = today()
    journal_entry.user_remark = f"Fair value movement for Biological Asset {asset.name}"

    if delta > 0:
        append_account(journal_entry, settings.biological_asset_account, debit=delta)
        append_account(journal_entry, settings.fair_value_gain_loss_account, credit=delta)
    else:
        append_account(journal_entry, settings.fair_value_gain_loss_account, debit=abs(delta))
        append_account(journal_entry, settings.biological_asset_account, credit=abs(delta))

    journal_entry.insert(ignore_permissions=True)
    journal_entry.submit()
    asset.db_set("last_journal_entry", journal_entry.name, update_modified=False)
    asset.db_set("last_posted_net_fair_value", asset.net_fair_value, update_modified=False)


def append_account(journal_entry, account, debit=0, credit=0):
    settings = frappe.get_single("Farm Management Settings")
    row = {
        "account": account,
        "debit_in_account_currency": flt(debit),
        "credit_in_account_currency": flt(credit),
    }
    if settings.default_cost_center:
        row["cost_center"] = settings.default_cost_center
    journal_entry.append("accounts", row)


def get_company(asset):
    if asset.linked_project:
        company = frappe.db.get_value("Project", asset.linked_project, "company")
        if company:
            return company
    return frappe.defaults.get_user_default("Company") or frappe.db.get_single_value(
        "Global Defaults", "default_company"
    )


def get_capitalization_comment(amount, source_doctype, source_name, remarks, quantity_delta):
    parts = []
    if amount:
        parts.append(f"Capitalised cost: {amount}")
    if quantity_delta:
        parts.append(f"Quantity movement: {quantity_delta}")
    if source_doctype and source_name:
        parts.append(f"Source: {source_doctype} {source_name}")
    if remarks:
        parts.append(remarks)
    return " | ".join(parts)
