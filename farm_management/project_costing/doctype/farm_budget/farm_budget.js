frappe.ui.form.on('Farm Budget', {
    refresh(frm) {
        calculate_budget_totals(frm);
    },
    farm_bom(frm) {
        if (!frm.doc.farm_bom) {
            return;
        }
        frappe.model.with_doc('Farm BOM', frm.doc.farm_bom, () => {
            const bom = frappe.model.get_doc('Farm BOM', frm.doc.farm_bom);
            if (bom.farm) {
                frm.set_value('farm', bom.farm);
            }
            if (bom.project) {
                frm.set_value('project', bom.project);
            }
            frm.clear_table('budget_items');
            (bom.bom_items || []).forEach((source) => {
                const row = frm.add_child('budget_items');
                row.item_category = source.item_category;
                row.item = source.item;
                row.item_description = source.item_description;
                row.budgeted_quantity = source.quantity;
                row.unit = source.unit;
                row.budgeted_unit_cost = source.unit_cost;
                row.budgeted_amount = source.total_cost;
            });
            frm.refresh_field('budget_items');
            calculate_budget_totals(frm);
        });
    }
});

frappe.ui.form.on('Farm Budget Item', {
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
                frappe.model.set_value(cdt, cdn, 'budgeted_unit_cost', flt(item.valuation_rate));
            }
            calculate_budget_row(frm, cdt, cdn);
        });
    },
    budgeted_quantity(frm, cdt, cdn) {
        calculate_budget_row(frm, cdt, cdn);
    },
    budgeted_unit_cost(frm, cdt, cdn) {
        calculate_budget_row(frm, cdt, cdn);
    },
    actual_amount(frm, cdt, cdn) {
        calculate_budget_row(frm, cdt, cdn);
    },
    budget_items_remove(frm) {
        calculate_budget_totals(frm);
    }
});

function calculate_budget_row(frm, cdt, cdn) {
    const row = frappe.get_doc(cdt, cdn);
    const budgeted = flt(row.budgeted_quantity) * flt(row.budgeted_unit_cost);
    const variance = flt(row.actual_amount) - budgeted;
    frappe.model.set_value(cdt, cdn, 'budgeted_amount', budgeted);
    frappe.model.set_value(cdt, cdn, 'variance', variance);
    frappe.model.set_value(cdt, cdn, 'variance_percent', budgeted ? flt((variance / budgeted) * 100, 2) : 0);
    frappe.model.set_value(cdt, cdn, 'variance_type', variance > 0 ? 'Adverse' : 'Favourable');
    calculate_budget_totals(frm);
}

function calculate_budget_totals(frm) {
    const rows = frm.doc.budget_items || [];
    const totalBudget = rows.reduce((sum, row) => sum + flt(row.budgeted_amount), 0);
    const totalActual = rows.reduce((sum, row) => sum + flt(row.actual_amount), 0);
    frm.set_value('total_budget', totalBudget);
    frm.set_value('total_actual', totalActual);
    frm.set_value('total_variance', totalActual - totalBudget);
}