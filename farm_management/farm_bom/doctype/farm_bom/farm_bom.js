frappe.ui.form.on('Farm BOM', {
    refresh(frm) {
        calculate_bom_total(frm);
    }
});

frappe.ui.form.on('Farm BOM Item', {
    item(frm, cdt, cdn) {
        const row = frappe.get_doc(cdt, cdn);
        if (!row.item) {
            return;
        }
        frappe.db.get_value('Item', row.item, ['item_name', 'stock_uom', 'valuation_rate']).then((r) => {
            const item = r.message || {};
            if (item.item_name) {
                frappe.model.set_value(cdt, cdn, 'item_description', item.item_name);
            }
            if (item.stock_uom) {
                frappe.model.set_value(cdt, cdn, 'unit', item.stock_uom);
            }
            if (item.valuation_rate != null) {
                frappe.model.set_value(cdt, cdn, 'unit_cost', flt(item.valuation_rate));
            }
            calculate_row_total(frm, cdt, cdn);
        });
    },
    quantity(frm, cdt, cdn) {
        calculate_row_total(frm, cdt, cdn);
    },
    unit_cost(frm, cdt, cdn) {
        calculate_row_total(frm, cdt, cdn);
    },
    bom_items_remove(frm) {
        calculate_bom_total(frm);
    }
});

function calculate_row_total(frm, cdt, cdn) {
    const row = frappe.get_doc(cdt, cdn);
    frappe.model.set_value(cdt, cdn, 'total_cost', flt(row.quantity) * flt(row.unit_cost));
    calculate_bom_total(frm);
}

function calculate_bom_total(frm) {
    const total = (frm.doc.bom_items || []).reduce((sum, row) => sum + flt(row.total_cost), 0);
    frm.set_value('total_estimated_cost', total);
}