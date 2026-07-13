frappe.ui.form.on("Standard Cost Calculation BOM", {
    refresh(frm) {
        calculate_standard_cost_totals(frm);
    },
    target_quantity(frm) {
        calculate_standard_cost_totals(frm);
    },
});

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
            calculate_standard_cost_row(frm, cdt, cdn);
        });
    },
    quantity(frm, cdt, cdn) {
        calculate_standard_cost_row(frm, cdt, cdn);
    },
    rate(frm, cdt, cdn) {
        calculate_standard_cost_row(frm, cdt, cdn);
    },
    standard_costs_remove(frm) {
        calculate_standard_cost_totals(frm);
    }
});

function calculate_standard_cost_row(frm, cdt, cdn) {
    const row = frappe.get_doc(cdt, cdn);
    frappe.model.set_value(cdt, cdn, 'amount', flt(row.quantity) * flt(row.rate));
    calculate_standard_cost_totals(frm);
}

function calculate_standard_cost_totals(frm) {
    const total = (frm.doc.standard_costs || []).reduce(
        (sum, row) => sum + flt(row.amount),
        0
    );
    frm.set_value("total_standard_cost", total);
    frm.set_value(
        "standard_cost_per_unit",
        flt(frm.doc.target_quantity) ? total / flt(frm.doc.target_quantity) : 0
    );
}
