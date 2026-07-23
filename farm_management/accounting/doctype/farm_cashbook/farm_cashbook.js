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
    debit(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (flt(row.debit) > 0 && flt(row.credit) !== 0) {
            frappe.model.set_value(cdt, cdn, 'credit', 0);
        }
        update_total(frm);
    },
    credit(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (flt(row.credit) > 0 && flt(row.debit) !== 0) {
            frappe.model.set_value(cdt, cdn, 'debit', 0);
        }
        update_total(frm);
    },
    entries_remove(frm) {
        update_total(frm);
    }
});

async function set_entry_queries(frm) {
    const ledger_filters = {is_group: 0};
    const cost_center_filters = {is_group: 0};
    if (frm.doc.farm) {
        const farm = await frappe.db.get_value('Farm', frm.doc.farm, 'owner_name');
        const company = farm.message && farm.message.owner_name;
        if (company) {
            ledger_filters.company = company;
            cost_center_filters.company = company;
        }
    }

    frm.fields_dict.entries.grid.get_field('account').get_query = () => ({
        filters: ledger_filters
    });

    frm.fields_dict.entries.grid.get_field('project').get_query = () => ({
        filters: {
            status: 'Open',
            ...(frm.doc.farm ? {farm: frm.doc.farm} : {})
        }
    });

    frm.fields_dict.entries.grid.get_field('cost_center').get_query = () => ({
        filters: cost_center_filters
    });
}

function update_total(frm) {
    const totals = (frm.doc.entries || []).reduce((value, row) => ({
        debit: value.debit + flt(row.debit),
        credit: value.credit + flt(row.credit),
    }), {debit: 0, credit: 0});
    frm.set_value('total_debit', totals.debit);
    frm.set_value('total_credit', totals.credit);
    frm.set_value('difference', totals.debit - totals.credit);
}
