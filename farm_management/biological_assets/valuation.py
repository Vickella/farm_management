import frappe
from frappe.utils import flt, today


def create_capitalization_document(
    biological_asset,
    amount=0,
    posting_date=None,
    capitalization_type="Other",
    source_doctype=None,
    source_name=None,
    remarks=None,
    quantity_delta=0,
    project=None,
    post_gl_entry=True,
    credit_account=None,
    accounting_source_doctype=None,
    accounting_source_name=None,
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
    doc.posting_date = posting_date or today()
    doc.capitalization_type = capitalization_type
    doc.amount = flt(amount)
    doc.quantity_delta = flt(quantity_delta)
    doc.source_doctype = source_doctype
    doc.source_name = source_name
    doc.project = project
    doc.post_gl_entry = 1 if post_gl_entry else 0
    doc.credit_account = credit_account
    doc.accounting_source_doctype = accounting_source_doctype
    doc.accounting_source_name = accounting_source_name
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


def get_or_create_biological_asset_for_livestock(livestock):
    if livestock.biological_asset:
        return livestock.biological_asset

    if not livestock.farm or not livestock.species:
        frappe.throw("Set Farm and Species before capitalizing livestock.")

    species = frappe.get_doc("Livestock Species", livestock.species)
    farm_type = species.farm_type or find_farm_type_for_managed_item(species.name)
    if not farm_type:
        frappe.throw(f"Set Farm Type on Livestock Species '{species.name}'.")

    filters = {
        "farm": livestock.farm,
        "farm_type": farm_type,
        "managed_item": species.name,
        "status": "Active",
    }
    existing = frappe.db.get_value("Biological Asset", filters, "name")
    if existing:
        return existing

    asset = frappe.new_doc("Biological Asset")
    asset.asset_name = f"{livestock.farm} - {species.name}"
    asset.farm = livestock.farm
    asset.asset_category = get_asset_category_for_species(species)
    asset.farm_type = farm_type
    asset.managed_item = species.name
    asset.output_item = frappe.db.get_value(
        "Farm Type Managed Item",
        {
            "parent": farm_type,
            "parenttype": "Farm Type",
            "farm_produce": species.name,
        },
        "default_output_item",
    )
    if not asset.output_item:
        frappe.throw(
            f"Configure the Default Output Item for {species.name} on Farm Type {farm_type}."
        )
    asset.livestock_breed = livestock.breed
    asset.status = "Active"
    asset.growth_stage = "Immature"
    asset.valuation_method = "Cost Accumulation"
    asset.acquisition_date = livestock.acquisition_date or livestock.date_of_birth or today()
    asset.quantity = 0
    asset.unit = "Bird" if asset.asset_category == "Poultry" else "Head"
    asset.initial_cost = 0
    asset.current_fair_value = 0
    asset.flags.allow_zero_initial_cost = True
    asset.insert(ignore_permissions=True)
    return asset.name


def find_farm_type_for_managed_item(managed_item):
    farm_type = frappe.db.get_value(
        "Farm Type Managed Item",
        {
            "farm_produce": managed_item,
            "parenttype": "Farm Type",
        },
        "parent",
    )
    if farm_type and frappe.db.get_value("Farm Type", farm_type, "is_active"):
        return farm_type
    return frappe.db.get_value("Farm Type", {"name": "Animal Husbandry", "is_active": 1}, "name")


def get_asset_category_for_species(species):
    if species.species_group == "Poultry":
        return "Poultry"
    return "Livestock"


@frappe.whitelist()
def repair_missing_livestock_assets():
    frappe.only_for("System Manager")
    repaired = []
    skipped = []
    livestock_records = frappe.get_all(
        "Livestock Individual",
        filters={"biological_asset": ["is", "not set"]},
        fields=["name"],
    )
    for row in livestock_records:
        try:
            livestock = frappe.get_doc("Livestock Individual", row.name)
            biological_asset = get_or_create_biological_asset_for_livestock(livestock)
            livestock.db_set("biological_asset", biological_asset, update_modified=False)
            if frappe.db.get_value("Livestock Individual", row.name, "biological_asset"):
                repaired.append(row.name)
            else:
                skipped.append(row.name)
        except Exception:
            skipped.append(row.name)
            frappe.log_error(
                title=f"Livestock Asset Repair Failed: {row.name}"[:140],
                message=frappe.get_traceback(),
            )

    return {"repaired": repaired, "skipped": skipped}


def apply_capitalization(capitalization):
    if not capitalization.biological_asset or (not flt(capitalization.amount) and not flt(capitalization.quantity_delta)):
        return

    asset = frappe.get_doc("Biological Asset", capitalization.biological_asset)

    if flt(capitalization.amount):
        if capitalization.capitalization_type == "Opening":
            asset.initial_cost = flt(asset.initial_cost) + flt(capitalization.amount)
        else:
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
    if capitalization.get("post_gl_entry"):
        create_capitalization_journal_entry(capitalization, asset)
    if flt(capitalization.amount):
        # The carrying amount is now represented in GL either by the generated
        # transfer journal or by the validated source invoice.
        asset.db_set("last_posted_net_fair_value", asset.net_fair_value, update_modified=False)


def reverse_capitalization(capitalization):
    if not capitalization.biological_asset:
        return

    asset = frappe.get_doc("Biological Asset", capitalization.biological_asset)
    if capitalization.capitalization_type == "Opening":
        asset.initial_cost = flt(asset.initial_cost) - flt(capitalization.amount)
    else:
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
    cancel_capitalization_journal_entry(capitalization)


def create_capitalization_journal_entry(capitalization, asset=None):
    amount = flt(capitalization.amount)
    if not amount:
        return

    from farm_management.install import setup_biological_asset_accounts

    setup_biological_asset_accounts()

    asset = asset or frappe.get_doc("Biological Asset", capitalization.biological_asset)
    biological_asset_account = get_biological_asset_account(asset)
    if capitalization.capitalization_type == "Birth":
        default_credit_account = get_fair_value_gain_loss_account(asset)
    elif capitalization.capitalization_type == "Opening":
        default_credit_account = get_temporary_opening_account(asset)
    else:
        default_credit_account = get_capital_work_in_progress_account(asset)
    credit_account = capitalization.get("credit_account") or default_credit_account
    if capitalization.get("credit_account"):
        validate_ledger_account(credit_account, get_company(asset), "Capitalization Credit Account")
    if not biological_asset_account or not credit_account:
        frappe.throw(
            "Configure the Biological Asset and capitalization credit accounts for this managed item."
        )

    company = get_company(asset)
    if not company:
        frappe.throw("Set Default Company in Farm Management Settings or on the linked Project.")

    journal_entry = frappe.new_doc("Journal Entry")
    journal_entry.voucher_type = (
        "Opening Entry" if capitalization.capitalization_type == "Opening" else "Journal Entry"
    )
    journal_entry.company = company
    journal_entry.posting_date = capitalization.posting_date or today()
    journal_entry.user_remark = (
        f"Biological asset capitalization for {asset.name} from "
        f"{capitalization.source_doctype or capitalization.doctype} "
        f"{capitalization.source_name or capitalization.name}"
    )

    append_account(
        journal_entry,
        biological_asset_account,
        debit=amount,
        project=capitalization.project or asset.linked_project,
    )
    append_account(
        journal_entry,
        credit_account,
        credit=amount,
        project=capitalization.project or asset.linked_project,
    )
    journal_entry.insert(ignore_permissions=True)
    journal_entry.submit()
    capitalization.db_set("journal_entry", journal_entry.name, update_modified=False)
    asset.db_set("last_journal_entry", journal_entry.name, update_modified=False)


def get_biological_asset_account(asset, settings=None):
    if isinstance(asset, str):
        asset = frappe.get_doc("Biological Asset", asset)

    managed_item_account = get_managed_item_account(asset, "biological_asset_account")
    if managed_item_account:
        return managed_item_account

    company = get_company(asset)
    if asset.farm_type and company:
        account_name = f"Biological Asset - {asset.farm_type}"
        account = frappe.db.get_value(
            "Account",
            {"account_name": account_name, "company": company, "is_group": 0},
            "name",
        )
        if account:
            return account

    return None


def get_capital_work_in_progress_account(asset, settings=None):
    account = get_managed_item_account(asset, "capital_work_in_progress_account")
    if account:
        return account
    company = get_company(asset)
    if not company:
        return None
    return frappe.db.get_value(
        "Account",
        {"account_name": "Biological Asset Capital Work In Progress", "company": company, "is_group": 0},
        "name",
    )


def get_fair_value_gain_loss_account(asset, settings=None):
    account = get_managed_item_account(asset, "fair_value_gain_loss_account")
    if account:
        return account
    company = get_company(asset)
    if not company:
        return None
    return frappe.db.get_value(
        "Account",
        {"account_name": "Biological Asset Fair Value Gain Loss", "company": company, "is_group": 0},
        "name",
    )


def get_managed_item_account(asset, fieldname):
    if isinstance(asset, str):
        asset = frappe.get_doc("Biological Asset", asset)
    if not asset.farm_type or not asset.managed_item:
        return None
    farm_type = frappe.get_doc("Farm Type", asset.farm_type)
    managed_item_key = (asset.managed_item or "").strip().lower()
    for row in farm_type.get("managed_items", []):
        if (row.farm_produce or "").strip().lower() == managed_item_key:
            return row.get(fieldname)
    return None


def cancel_capitalization_journal_entry(capitalization):
    if not capitalization.journal_entry or not frappe.db.exists("Journal Entry", capitalization.journal_entry):
        return

    journal_entry = frappe.get_doc("Journal Entry", capitalization.journal_entry)
    if journal_entry.docstatus == 1:
        journal_entry.cancel()


def reduce_asset_quantity(biological_asset, quantity, source_doctype=None, source_name=None, empty_status="Harvested"):
    quantity = flt(quantity)
    if not biological_asset or not quantity:
        return 0

    asset = frappe.get_doc("Biological Asset", biological_asset)
    if asset.asset_category != "Crops in Growth" and quantity > flt(asset.quantity):
        frappe.throw("Harvest quantity cannot exceed Biological Asset quantity.")

    value_before = flt(asset.net_fair_value)
    asset.quantity = flt(asset.quantity) - quantity
    if flt(asset.quantity) <= 0:
        asset.quantity = 0
        asset.status = empty_status or "Harvested"

    asset.recalculate_valuation(scale_by_quantity=True)
    asset.last_valuation_date = today()
    asset.add_comment(
        "Info",
        get_capitalization_comment(0, source_doctype, source_name, "Harvest quantity reduction", -quantity),
    )
    asset.save(ignore_permissions=True)
    return value_before - flt(asset.net_fair_value)


def get_asset_valuation_snapshot(biological_asset):
    asset = frappe.get_doc("Biological Asset", biological_asset)
    return frappe.as_json(
        {
            fieldname: asset.get(fieldname)
            for fieldname in (
                "quantity",
                "initial_cost",
                "capitalized_cost",
                "current_fair_value",
                "cost_to_sell",
                "net_fair_value",
                "accumulated_gain_loss",
                "previous_quantity",
                "status",
                "last_valuation_date",
                "last_posted_net_fair_value",
                "last_journal_entry",
            )
        }
    )


def restore_asset_quantity(
    biological_asset,
    quantity,
    asset_value_reduction=0,
    source_doctype=None,
    source_name=None,
    valuation_snapshot=None,
):
    quantity = flt(quantity)
    if not biological_asset or not quantity:
        return

    asset = frappe.get_doc("Biological Asset", biological_asset)
    if valuation_snapshot:
        snapshot = (
            frappe.parse_json(valuation_snapshot)
            if isinstance(valuation_snapshot, str)
            else valuation_snapshot
        )
        for fieldname in (
            "quantity",
            "initial_cost",
            "capitalized_cost",
            "current_fair_value",
            "cost_to_sell",
            "net_fair_value",
            "accumulated_gain_loss",
            "previous_quantity",
            "status",
            "last_valuation_date",
            "last_posted_net_fair_value",
            "last_journal_entry",
        ):
            if fieldname in snapshot:
                asset.set(fieldname, snapshot[fieldname])
        asset.add_comment(
            "Info",
            get_capitalization_comment(
                0, source_doctype, source_name, "Quantity cancellation restored exact valuation snapshot", quantity
            ),
        )
        asset.flags.ignore_validate = True
        asset.save(ignore_permissions=True)
        if "last_valuation_date" in snapshot:
            asset.db_set(
                "last_valuation_date",
                snapshot["last_valuation_date"],
                update_modified=False,
            )
        return

    asset.quantity = flt(asset.quantity) + quantity
    if asset.status in ("Harvested", "Sold", "Dead Loss"):
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


def create_asset_outflow_journal_entry(
    biological_asset,
    amount,
    posting_date=None,
    project=None,
    source_doctype=None,
    source_name=None,
    remarks=None,
    debit_account=None,
):
    amount = flt(amount)
    if not biological_asset or not amount:
        return None

    from farm_management.install import setup_biological_asset_accounts

    setup_biological_asset_accounts()

    asset = frappe.get_doc("Biological Asset", biological_asset)
    biological_asset_account = get_biological_asset_account(asset)
    outflow_account = debit_account or get_fair_value_gain_loss_account(asset)
    if not biological_asset_account or not outflow_account:
        frappe.throw(
            "Set Biological Asset Account and Fair Value Gain/Loss Account on the managed item row in Farm Type."
        )

    company = get_company(asset)
    if not company:
        frappe.throw("Set Default Company in Farm Management Settings or on the linked Project.")

    journal_entry = frappe.new_doc("Journal Entry")
    journal_entry.voucher_type = "Journal Entry"
    journal_entry.company = company
    journal_entry.posting_date = posting_date or today()
    journal_entry.user_remark = remarks or (
        f"Biological asset outflow for {asset.name}"
        + (f" from {source_doctype} {source_name}" if source_doctype and source_name else "")
    )

    append_account(
        journal_entry,
        outflow_account,
        debit=amount,
        project=project or asset.linked_project,
    )
    append_account(
        journal_entry,
        biological_asset_account,
        credit=amount,
        project=project or asset.linked_project,
    )
    journal_entry.insert(ignore_permissions=True)
    journal_entry.submit()
    asset.db_set("last_journal_entry", journal_entry.name, update_modified=False)
    asset.db_set("last_posted_net_fair_value", asset.net_fair_value, update_modified=False)
    return journal_entry.name


def get_biological_asset_cost_of_sales_account(asset):
    if isinstance(asset, str):
        asset = frappe.get_doc("Biological Asset", asset)
    company = get_company(asset)
    settings = frappe.get_single("Farm Management Settings")
    configured = settings.get("biological_asset_cost_of_sales_account")
    if configured:
        validate_ledger_account(configured, company, "Biological Asset Cost of Sales")
        return configured
    return frappe.db.get_value(
        "Account",
        {"account_name": "Biological Asset Cost of Sales", "company": company, "is_group": 0},
        "name",
    )


def get_temporary_opening_account(asset):
    company = get_company(asset)
    if not company:
        return None
    return frappe.db.get_value(
        "Account",
        {"company": company, "account_type": "Temporary", "is_group": 0},
        "name",
    )


def get_capitalization_source_account(
    biological_asset,
    source_doctype,
    source_name,
    amount,
    project=None,
):
    """Return one posted debit account with enough uncapitalized source value."""
    if not source_doctype or not source_name:
        frappe.throw("Select a submitted accounting source before capitalizing this cost.")
    source = frappe.get_doc(source_doctype, source_name)
    if source.docstatus != 1:
        frappe.throw(f"{source_doctype} {source_name} must be submitted.")
    asset = frappe.get_doc("Biological Asset", biological_asset)
    company = get_company(asset)
    if source.get("company") and source.company != company:
        frappe.throw(f"{source_doctype} {source_name} must belong to company {company}.")

    filters = {
        "company": company,
        "voucher_type": source_doctype,
        "voucher_no": source_name,
        "is_cancelled": 0,
    }
    if project:
        filters["project"] = project
    debit_rows = frappe.get_all(
        "GL Entry",
        filters=filters,
        fields=["account", "sum(debit - credit) as net_debit"],
        group_by="account",
    )
    candidates = []
    stock_accounts = []
    for row in debit_rows:
        net_debit = flt(row.net_debit)
        if net_debit <= 0:
            continue
        if frappe.db.get_value("Account", row.account, "account_type") == "Stock":
            stock_accounts.append(row.account)
            continue
        used = flt(
            frappe.db.get_value(
                "Biological Asset Capitalization",
                {
                    "accounting_source_doctype": source_doctype,
                    "accounting_source_name": source_name,
                    "credit_account": row.account,
                    "docstatus": 1,
                },
                "sum(amount)",
            )
        )
        available = net_debit - used
        if available + 0.005 >= flt(amount):
            candidates.append((row.account, available))
    exact = [row for row in candidates if abs(row[1] - flt(amount)) < 0.01]
    if len(exact) == 1:
        return exact[0][0]
    if len(candidates) == 1:
        return candidates[0][0]
    if not candidates:
        if stock_accounts:
            frappe.throw(
                "Stock In Hand accounts can only be changed by Stock Transactions. "
                "Issue the consumed Item with a submitted Material Issue against this Project; "
                "Farm Management will capitalize that issue automatically."
            )
        frappe.throw(
            f"{source_doctype} {source_name} has no uncapitalized posted debit of {flt(amount)} "
            f"for company {company}" + (f" and project {project}" if project else "") + "."
        )
    frappe.throw(
        f"{source_doctype} {source_name} has multiple eligible debit accounts. "
        "Use a source document/project combination with one identifiable cost debit."
    )


def create_asset_sale_proceeds_journal_entry(
    biological_asset,
    amount,
    posting_date=None,
    project=None,
    source_doctype=None,
    source_name=None,
):
    amount = flt(amount)
    if not biological_asset or not amount:
        return None

    from farm_management.install import setup_biological_asset_sales_accounts

    setup_biological_asset_sales_accounts()

    asset = frappe.get_doc("Biological Asset", biological_asset)
    company = get_company(asset)
    if not company:
        frappe.throw("Set Default Company in Farm Management Settings or on the linked Project.")

    settings = frappe.get_single("Farm Management Settings")
    if settings.biological_asset_sales_receivable_account:
        validate_ledger_account(settings.biological_asset_sales_receivable_account, company, "Biological Asset Sales Receivable")
    if settings.biological_asset_sales_income_account:
        validate_ledger_account(settings.biological_asset_sales_income_account, company, "Biological Asset Sales Income")

    receivable_account = settings.biological_asset_sales_receivable_account or frappe.db.get_value(
        "Account",
        {"account_name": "Biological Asset Sales Receivable", "company": company, "is_group": 0},
        "name",
    )
    income_account = settings.biological_asset_sales_income_account or frappe.db.get_value(
        "Account",
        {"account_name": "Biological Asset Sales Income", "company": company, "is_group": 0},
        "name",
    )
    if not receivable_account or not income_account:
        frappe.throw("Biological Asset sales accounts could not be created for the selected company.")

    journal_entry = frappe.new_doc("Journal Entry")
    journal_entry.voucher_type = "Journal Entry"
    journal_entry.company = company
    journal_entry.posting_date = posting_date or today()
    journal_entry.user_remark = (
        f"Biological asset sale proceeds for {asset.name}"
        + (f" from {source_doctype} {source_name}" if source_doctype and source_name else "")
    )
    append_account(journal_entry, receivable_account, debit=amount, project=project or asset.linked_project)
    append_account(journal_entry, income_account, credit=amount, project=project or asset.linked_project)
    journal_entry.insert(ignore_permissions=True)
    journal_entry.submit()
    asset.db_set("last_journal_entry", journal_entry.name, update_modified=False)
    return journal_entry.name


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
            asset = frappe.get_doc("Biological Asset", asset_name)
            cwip_account = get_capital_work_in_progress_account(asset)
            project_rows = [
                row for row in stock_entry.get("items", [])
                if (row.get("project") or stock_entry.get("project")) == project
            ]
            invalid_rows = [row.idx for row in project_rows if row.get("expense_account") != cwip_account]
            if invalid_rows:
                frappe.throw(
                    "Material Issue rows capitalized to a Biological Asset must post to its Capital Work In Progress "
                    f"account. Correct rows: {', '.join(str(idx) for idx in invalid_rows)}."
                )
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


def create_fair_value_journal_entry(asset, delta=None, posting_date=None):
    from farm_management.install import setup_biological_asset_accounts

    setup_biological_asset_accounts()

    biological_asset_account = get_biological_asset_account(asset)
    fair_value_gain_loss_account = get_fair_value_gain_loss_account(asset)
    if not biological_asset_account or not fair_value_gain_loss_account:
        return

    company = get_company(asset)
    if not company:
        return

    delta = flt(delta) if delta is not None else flt(asset.net_fair_value) - flt(asset.last_posted_net_fair_value)
    if not delta:
        return

    journal_entry = frappe.new_doc("Journal Entry")
    journal_entry.voucher_type = "Journal Entry"
    journal_entry.company = company
    journal_entry.posting_date = posting_date or today()
    journal_entry.user_remark = f"Fair value movement for Biological Asset {asset.name}"

    if delta > 0:
        append_account(journal_entry, biological_asset_account, debit=delta, project=asset.linked_project)
        append_account(journal_entry, fair_value_gain_loss_account, credit=delta, project=asset.linked_project)
    else:
        append_account(journal_entry, fair_value_gain_loss_account, debit=abs(delta), project=asset.linked_project)
        append_account(journal_entry, biological_asset_account, credit=abs(delta), project=asset.linked_project)

    journal_entry.insert(ignore_permissions=True)
    journal_entry.submit()
    asset.db_set("last_journal_entry", journal_entry.name, update_modified=False)
    asset.db_set("last_posted_net_fair_value", asset.net_fair_value, update_modified=False)


@frappe.whitelist()
def get_biological_asset_gl_reconciliation(company=None, posting_date=None, throw_on_difference=False):
    """Reconcile each IAS 41 subledger account to posted ERPNext GL entries."""
    frappe.has_permission("Biological Asset", ptype="read", throw=True)
    company = company or frappe.get_single("Farm Management Settings").default_company
    if not company:
        frappe.throw("Select a company for Biological Asset GL reconciliation.")

    configured_accounts = frappe.get_all(
            "Farm Type Managed Item",
            filters={"biological_asset_account": ["is", "set"]},
            pluck="biological_asset_account",
        )
    accounts = set(
        frappe.get_all(
            "Account",
            filters={"name": ["in", configured_accounts or [""]], "company": company, "is_group": 0},
            pluck="name",
        )
    )
    accounts.update(
        frappe.get_all(
            "Account",
            filters={
                "company": company,
                "is_group": 0,
                "account_name": ["like", "Biological Asset - %"],
            },
            pluck="name",
        )
    )
    assets = frappe.get_all(
        "Biological Asset",
        filters={"status": ["not in", ["Cancelled"]]},
        fields=["name", "net_fair_value"],
    )
    subledger = {}
    for row in assets:
        asset = frappe.get_doc("Biological Asset", row.name)
        if get_company(asset) != company:
            continue
        account = get_biological_asset_account(asset)
        if not account:
            frappe.throw(f"Biological Asset {asset.name} has no configured ledger account.")
        accounts.add(account)
        subledger[account] = subledger.get(account, 0) + flt(asset.net_fair_value)

    filters = {"company": company, "is_cancelled": 0, "account": ["in", list(accounts) or [""]]}
    gl_rows = frappe.get_all(
        "GL Entry",
        filters=filters,
        fields=["account", "sum(debit - credit) as balance"],
        group_by="account",
    )
    gl_balances = {row.account: flt(row.balance) for row in gl_rows}
    rows = []
    for account in sorted(accounts):
        difference = flt(subledger.get(account)) - flt(gl_balances.get(account))
        rows.append(
            {
                "account": account,
                "subledger_value": subledger.get(account, 0),
                "gl_balance": gl_balances.get(account, 0),
                "difference": difference,
                "status": "Reconciled" if abs(difference) < 0.01 else "Mismatch",
            }
        )
    if throw_on_difference and any(row["status"] == "Mismatch" for row in rows):
        frappe.throw("Biological Asset subledger does not reconcile to the General Ledger.")
    return rows


def validate_ledger_account(account, company, label):
    account_doc = frappe.db.get_value(
        "Account",
        account,
        ["name", "is_group", "company"],
        as_dict=True,
    )
    if not account_doc:
        frappe.throw(f"Select a valid account for {label}.")
    if account_doc.is_group:
        frappe.throw(f"{label} must be a ledger account, not a group account.")
    if account_doc.company != company:
        frappe.throw(f"{label} must belong to company {company}.")


def append_account(journal_entry, account, debit=0, credit=0, project=None, party_type=None, party=None):
    settings = frappe.get_single("Farm Management Settings")
    row = {
        "account": account,
        "debit_in_account_currency": flt(debit),
        "credit_in_account_currency": flt(credit),
    }
    if settings.default_cost_center:
        row["cost_center"] = settings.default_cost_center
    if project:
        row["project"] = project
    if party_type and party:
        row["party_type"] = party_type
        row["party"] = party
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
