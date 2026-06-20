import frappe
from frappe.utils import flt, today


def create_capitalization_document(
    biological_asset,
    amount=0,
    capitalization_type="Other",
    source_doctype=None,
    source_name=None,
    remarks=None,
    quantity_delta=0,
    project=None,
    submit=True,
):
    if not biological_asset or (not flt(amount) and not flt(quantity_delta)):
        return None

    if source_doctype and source_name:
        existing = frappe.db.get_value(
            "Biological Asset Capitalization",
            {
                "biological_asset": biological_asset,
                "source_doctype": source_doctype,
                "source_name": source_name,
                "capitalization_type": capitalization_type,
                "docstatus": ["!=", 2],
            },
            "name",
        )
        if existing:
            return existing

    doc = frappe.new_doc("Biological Asset Capitalization")
    doc.biological_asset = biological_asset
    doc.posting_date = today()
    doc.capitalization_type = capitalization_type
    doc.amount = flt(amount)
    doc.quantity_delta = flt(quantity_delta)
    doc.source_doctype = source_doctype
    doc.source_name = source_name
    doc.project = project
    doc.remarks = remarks
    doc.insert(ignore_permissions=True)
    if submit:
        doc.submit()
    return doc.name


def capitalize_asset_cost(
    biological_asset,
    amount,
    source_doctype=None,
    source_name=None,
    remarks=None,
    quantity_delta=0,
    create_journal_entry=False,
):
    return create_capitalization_document(
        biological_asset=biological_asset,
        amount=amount,
        capitalization_type="Other",
        source_doctype=source_doctype,
        source_name=source_name,
        remarks=remarks,
        quantity_delta=quantity_delta,
        submit=True,
    )


def apply_capitalization(capitalization):
    if not capitalization.biological_asset or (not flt(capitalization.amount) and not flt(capitalization.quantity_delta)):
        return

    asset = frappe.get_doc("Biological Asset", capitalization.biological_asset)

    if flt(capitalization.amount):
        asset.capitalized_cost = flt(asset.capitalized_cost) + flt(capitalization.amount)

    if flt(capitalization.quantity_delta):
        asset.quantity = flt(asset.quantity) + flt(capitalization.quantity_delta)

    asset.recalculate_valuation()
    asset.last_valuation_date = capitalization.posting_date or today()
    asset.add_comment(
        "Info",
        get_capitalization_comment(
            capitalization.amount,
            capitalization.source_doctype,
            capitalization.source_name,
            capitalization.remarks,
            capitalization.quantity_delta,
        ),
    )
    asset.save(ignore_permissions=True)


def reverse_capitalization(capitalization):
    if not capitalization.biological_asset:
        return

    asset = frappe.get_doc("Biological Asset", capitalization.biological_asset)
    asset.capitalized_cost = flt(asset.capitalized_cost) - flt(capitalization.amount)
    asset.quantity = flt(asset.quantity) - flt(capitalization.quantity_delta)
    if flt(asset.quantity) < 0:
        asset.quantity = 0
    if flt(asset.quantity) == 0:
        asset.status = "Harvested"
    elif asset.status == "Harvested":
        asset.status = "Active"
    asset.recalculate_valuation()
    asset.last_valuation_date = today()
    asset.add_comment(
        "Info",
        get_capitalization_comment(
            -flt(capitalization.amount),
            capitalization.doctype,
            capitalization.name,
            "Capitalization cancelled",
            -flt(capitalization.quantity_delta),
        ),
    )
    asset.save(ignore_permissions=True)


def reduce_asset_quantity(biological_asset, quantity, source_doctype=None, source_name=None):
    quantity = flt(quantity)
    if not biological_asset or not quantity:
        return 0

    asset = frappe.get_doc("Biological Asset", biological_asset)
    if quantity > flt(asset.quantity):
        frappe.throw("Harvest quantity cannot exceed Biological Asset quantity.")

    value_before = flt(asset.net_fair_value)
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
    return value_before - flt(asset.net_fair_value)


def restore_asset_quantity(biological_asset, quantity, asset_value_reduction=0, source_doctype=None, source_name=None):
    quantity = flt(quantity)
    if not biological_asset or not quantity:
        return

    asset = frappe.get_doc("Biological Asset", biological_asset)
    asset.quantity = flt(asset.quantity) + quantity
    if asset.status == "Harvested":
        asset.status = "Active"

    if flt(asset_value_reduction):
        asset.current_fair_value = flt(asset.current_fair_value) + flt(asset_value_reduction)
        asset.net_fair_value = flt(asset.net_fair_value) + flt(asset_value_reduction)

    asset.previous_quantity = flt(asset.quantity)
    asset.last_valuation_date = today()
    asset.add_comment(
        "Info",
        get_capitalization_comment(0, source_doctype, source_name, "Harvest cancellation quantity restored", quantity),
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
        assets = frappe.get_all(
            "Biological Asset",
            filters={"linked_project": project, "status": "Active"},
            pluck="name",
        )
        if len(assets) > 1:
            frappe.throw(
                f"Project {project} has multiple active Biological Assets. "
                "Link material issue costs to one active asset only."
            )
        asset_name = assets[0] if assets else None
        if asset_name and amount:
            create_capitalization_document(
                biological_asset=asset_name,
                amount=amount,
                capitalization_type="Material Issue",
                source_doctype=stock_entry.doctype,
                source_name=stock_entry.name,
                remarks=f"Material Issue capitalized from Project {project}",
                project=project,
            )


def cancel_project_material_issue(stock_entry, method=None):
    capitalizations = frappe.get_all(
        "Biological Asset Capitalization",
        filters={
            "source_doctype": stock_entry.doctype,
            "source_name": stock_entry.name,
            "docstatus": 1,
        },
        pluck="name",
    )
    for name in capitalizations:
        frappe.get_doc("Biological Asset Capitalization", name).cancel()


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
    settings = frappe.get_single("Farm Management Settings")
    if settings.default_company:
        return settings.default_company
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
