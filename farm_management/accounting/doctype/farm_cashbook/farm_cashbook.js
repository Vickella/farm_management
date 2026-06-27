frappe.ui.form.on('Farm Cashbook', {
    refresh(frm) {
        frm.set_query('project', () => ({
            filters: {status: 'Open'}
        }));
        set_account_queries(frm);
    },
    farm(frm) {
        set_account_queries(frm);
    }
});

function set_account_queries(frm) {
    const ledger_filters = {
        is_group: 0
    };

    frm.set_query('debit_account', () => ({
        filters: ledger_filters
    }));

    frm.set_query('credit_account', () => ({
        filters: ledger_filters
    }));
}
