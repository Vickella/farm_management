frappe.ui.form.on('Standard Cost Calculation BOM Item', {
    item(frm, cdt, cdn) {
        const row = frappe.get_doc(cdt, cdn);
        if (!row.item) {
            return;
        }
        frappe.db.get_value('Item', row.item, ['stock_uom', 'valuation_rate']).then((r) => {
            const item = r.message || {};
            if (item.stock_uom) {
                frappe.model.set_value(cdt, cdn, 'unit', item.stock_uom);
            }
            if (item.valuation_rate != null) {
                frappe.model.set_value(cdt, cdn, 'rate', flt(item.valuation_rate));
            }
            calculate_standard_cost_row(cdt, cdn);
        });
    },
    quantity(frm, cdt, cdn) {
        calculate_standard_cost_row(cdt, cdn);
    },
    rate(frm, cdt, cdn) {
        calculate_standard_cost_row(cdt, cdn);
    }
});

function calculate_standard_cost_row(cdt, cdn) {
    const row = frappe.get_doc(cdt, cdn);
    frappe.model.set_value(cdt, cdn, 'amount', flt(row.quantity) * flt(row.rate));
}