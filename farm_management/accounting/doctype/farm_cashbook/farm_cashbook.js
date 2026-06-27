frappe.ui.form.on('Farm Cashbook', {
    refresh(frm) {
        frm.set_query('project', () => ({
            filters: {status: 'Open'}
        }));
        set_payment_account_query(frm);
    },
    farm(frm) {
        set_payment_account_query(frm);
    }
});

function set_payment_account_query(frm) {
    frm.set_query('payment_account', () => {
        const filters = {
            is_group: 0,
            account_type: ['in', ['Bank', 'Cash']]
        };
        return {filters};
    });
}