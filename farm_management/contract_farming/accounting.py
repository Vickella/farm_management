import frappe
from frappe.utils import flt

from farm_management.biological_assets.valuation import append_account


def get_contract_company(agreement):
    agreement = agreement if hasattr(agreement, "farm") else frappe.get_doc("Contract Farming Agreement", agreement)
    company = frappe.db.get_value("Farm", agreement.farm, "owner_name")
    if not company:
        frappe.throw(f"Set Farm Owner Company on Farm {agreement.farm}.")
    return company


def get_contract_account(account_name, company, settings_field=None):
    settings = frappe.get_single("Farm Management Settings")
    configured_account = settings.get(settings_field) if settings_field else None
    if configured_account:
        validate_ledger_account(configured_account, company, account_name)
        return configured_account

    from farm_management.install import setup_contract_farming_accounts

    setup_contract_farming_accounts(company)
    account = frappe.db.get_value(
        "Account",
        {"account_name": account_name, "company": company, "is_group": 0},
        "name",
    )
    if not account:
        frappe.throw(f"Could not create or find account: {account_name}")
    return account


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


def create_input_loan_journal(disbursement):
    amount = flt(disbursement.total_value)
    if not amount:
        return None

    agreement = frappe.get_doc("Contract Farming Agreement", disbursement.agreement)
    company = get_contract_company(agreement)

    if agreement.contract_type == "Receiving Contract (Liability)":
        return create_received_input_journal(disbursement, agreement, company, amount)

    receivable = get_contract_account(
        "Contract Farming Input Loans Receivable",
        company,
        "contract_input_loans_receivable_account",
    )
    clearing = get_contract_account(
        "Contract Farming Input Clearing",
        company,
        "contract_input_clearing_account",
    )

    journal_entry = frappe.new_doc("Journal Entry")
    journal_entry.voucher_type = "Journal Entry"
    journal_entry.company = company
    journal_entry.posting_date = disbursement.disbursement_date
    journal_entry.user_remark = f"Input loan disbursement for {disbursement.agreement}"
    append_account(journal_entry, receivable, debit=amount)
    append_account(journal_entry, clearing, credit=amount)
    journal_entry.insert(ignore_permissions=True)
    journal_entry.submit()
    return journal_entry.name


def create_received_input_journal(disbursement, agreement, company, amount):
    input_expense = get_contract_account(
        "Contract Farming Inputs Received Expense",
        company,
        "contract_inputs_received_expense_account",
    )
    liability = get_contract_account(
        "Contract Farming Deferred Liability",
        company,
        "contract_farming_liability_account",
    )
    journal_entry = frappe.new_doc("Journal Entry")
    journal_entry.voucher_type = "Journal Entry"
    journal_entry.company = company
    journal_entry.posting_date = disbursement.disbursement_date
    journal_entry.user_remark = f"Inputs received under contract {agreement.name}"
    append_account(journal_entry, input_expense, debit=amount, project=agreement.linked_project)
    append_account(journal_entry, liability, credit=amount, project=agreement.linked_project)
    journal_entry.insert(ignore_permissions=True)
    journal_entry.submit()
    return journal_entry.name


def create_harvest_recovery_journal(recovery):
    gross_payment = flt(recovery.gross_payment)
    loan_recovery = flt(recovery.loan_recovery_amount)
    net_payment = flt(recovery.net_payment)
    if not gross_payment:
        return None

    agreement = frappe.get_doc("Contract Farming Agreement", recovery.agreement)
    company = get_contract_company(agreement)

    if agreement.contract_type == "Receiving Contract (Liability)":
        return create_receiving_harvest_journal(recovery, agreement, company)

    purchases = get_contract_account(
        "Contract Farming Harvest Purchases",
        company,
        "contract_harvest_purchases_account",
    )
    receivable = get_contract_account(
        "Contract Farming Input Loans Receivable",
        company,
        "contract_input_loans_receivable_account",
    )
    grower_payable = get_contract_account(
        "Contract Farming Grower Payable",
        company,
        "contract_grower_payable_account",
    )

    journal_entry = frappe.new_doc("Journal Entry")
    journal_entry.voucher_type = "Journal Entry"
    journal_entry.company = company
    journal_entry.posting_date = recovery.recovery_date
    journal_entry.user_remark = f"Harvest recovery for {recovery.agreement}"
    append_account(journal_entry, purchases, debit=gross_payment)
    if loan_recovery:
        append_account(journal_entry, receivable, credit=loan_recovery)
    if net_payment:
        append_account(journal_entry, grower_payable, credit=net_payment)
    journal_entry.insert(ignore_permissions=True)
    journal_entry.submit()
    return journal_entry.name


def create_receiving_harvest_journal(recovery, agreement, company):
    from erpnext.accounts.party import get_party_account

    if not agreement.sponsor_customer:
        frappe.throw("Sponsor Customer is required for a Receiving Contract.")
    income = get_contract_account(
        "Contract Farming Income", company, "contract_farming_income_account"
    )
    liability = get_contract_account(
        "Contract Farming Deferred Liability", company, "contract_farming_liability_account"
    )
    receivable = get_party_account("Customer", agreement.sponsor_customer, company)
    gross_payment = flt(recovery.gross_payment)
    loan_recovery = flt(recovery.loan_recovery_amount)
    net_payment = flt(recovery.net_payment)

    journal_entry = frappe.new_doc("Journal Entry")
    journal_entry.voucher_type = "Journal Entry"
    journal_entry.company = company
    journal_entry.posting_date = recovery.recovery_date
    journal_entry.user_remark = f"Harvest delivered under receiving contract {agreement.name}"
    if net_payment:
        append_account(
            journal_entry,
            receivable,
            debit=net_payment,
            project=agreement.linked_project,
            party_type="Customer",
            party=agreement.sponsor_customer,
        )
    if loan_recovery:
        append_account(journal_entry, liability, debit=loan_recovery, project=agreement.linked_project)
    append_account(journal_entry, income, credit=gross_payment, project=agreement.linked_project)
    journal_entry.insert(ignore_permissions=True)
    journal_entry.submit()
    return journal_entry.name


def cancel_journal_entry(journal_entry_name):
    if not journal_entry_name or not frappe.db.exists("Journal Entry", journal_entry_name):
        return
    journal_entry = frappe.get_doc("Journal Entry", journal_entry_name)
    if journal_entry.docstatus == 1:
        journal_entry.cancel()
