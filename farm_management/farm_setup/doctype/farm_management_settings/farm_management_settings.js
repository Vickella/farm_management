frappe.ui.form.on('Farm Management Settings', {
    refresh(frm) {
        set_account_queries(frm);
    }
});

function set_account_queries(frm) {
    const account_fields = [
        'contract_input_loans_receivable_account',
        'contract_input_clearing_account',
        'contract_harvest_purchases_account',
        'contract_grower_payable_account',
        'biological_asset_sales_receivable_account',
        'biological_asset_sales_income_account'
    ];

    account_fields.forEach((fieldname) => {
        frm.set_query(fieldname, () => ({
            filters: {is_group: 0}
        }));
    });
}
