frappe.ui.form.on('Farm Cashbook', {
    refresh(frm) {
        frm.set_query('project', () => ({
            filters: {status: 'Open'}
        }));
        set_entry_queries(frm);
        update_total(frm);
    },
    farm(frm) {
        set_entry_queries(frm);
    },
    entries_add(frm) {
        update_total(frm);
    },
    entries_remove(frm) {
        update_total(frm);
    }
});

frappe.ui.form.on('Farm Cashbook Entry', {
    amount(frm) {
        update_total(frm);
    },
    entries_remove(frm) {
        update_total(frm);
    }
});

function set_entry_queries(frm) {
    const ledger_filters = {is_group: 0};

    frm.fields_dict.entries.grid.get_field('debit_account').get_query = () => ({
        filters: ledger_filters
    });

    frm.fields_dict.entries.grid.get_field('credit_account').get_query = () => ({
        filters: ledger_filters
    });

    frm.fields_dict.entries.grid.get_field('project').get_query = () => ({
        filters: {status: 'Open'}
    });

    frm.fields_dict.entries.grid.get_field('cost_center').get_query = () => ({
        filters: {is_group: 0}
    });
}

function update_total(frm) {
    const total = (frm.doc.entries || []).reduce((sum, row) => sum + flt(row.amount), 0);
    frm.set_value('total_amount', total);
}
