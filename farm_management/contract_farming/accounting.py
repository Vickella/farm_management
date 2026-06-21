import frappe
from frappe.utils import flt

from farm_management.biological_assets.valuation import append_account


def get_company():
    settings = frappe.get_single("Farm Management Settings")
    return settings.default_company or frappe.defaults.get_user_default("Company") or frappe.db.get_single_value(
        "Global Defaults", "default_company"
    )


def get_contract_account(account_name, company):
    from farm_management.install import setup_contract_farming_accounts

    setup_contract_farming_accounts()
    account = frappe.db.get_value(
        "Account",
        {"account_name": account_name, "company": company, "is_group": 0},
        "name",
    )
    if not account:
        frappe.throw(f"Could not create or find account: {account_name}")
    return account


def create_input_loan_journal(disbursement):
    amount = flt(disbursement.value)
    if not amount:
        return None

    company = get_company()
    if not company:
        frappe.throw("Set Default Company in Farm Management Settings before posting contract farming accounting.")

    receivable = get_contract_account("Contract Farming Input Loans Receivable", company)
    clearing = get_contract_account("Contract Farming Input Clearing", company)

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


def create_harvest_recovery_journal(recovery):
    gross_payment = flt(recovery.gross_payment)
    loan_recovery = flt(recovery.loan_recovery_amount)
    net_payment = flt(recovery.net_payment)
    if not gross_payment:
        return None

    company = get_company()
    if not company:
        frappe.throw("Set Default Company in Farm Management Settings before posting contract farming accounting.")

    purchases = get_contract_account("Contract Farming Harvest Purchases", company)
    receivable = get_contract_account("Contract Farming Input Loans Receivable", company)
    grower_payable = get_contract_account("Contract Farming Grower Payable", company)

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


def cancel_journal_entry(journal_entry_name):
    if not journal_entry_name or not frappe.db.exists("Journal Entry", journal_entry_name):
        return
    journal_entry = frappe.get_doc("Journal Entry", journal_entry_name)
    if journal_entry.docstatus == 1:
        journal_entry.cancel()
