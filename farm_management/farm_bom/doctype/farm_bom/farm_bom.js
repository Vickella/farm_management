frappe.ui.form.on('Farm BOM', {
    refresh(frm) {
        calculate_bom_total(frm);
        if (!frm.is_new()) {
            frm.add_custom_button(__('Create Budget'), () => {
                frappe.new_doc('Farm Budget', {
                    farm_bom: frm.doc.name,
                    farm: frm.doc.farm,
                    project: frm.doc.project,
                    budget_period_start: frm.doc.planned_start_date,
                    budget_period_end: frm.doc.planned_end_date,
                });
            }, __('Planning'));
        }
    },
    project(frm) {
        if (!frm.doc.project) {
            return;
        }
        frappe.db.get_value(
            'Project',
            frm.doc.project,
            [
                'farm',
                'agriculture_project_type',
                'project_quantity',
                'project_unit',
                'expected_start_date',
                'expected_end_date',
            ]
        ).then((r) => {
            const project = r.message || {};
            frm.set_value('farm', project.farm || null);
            frm.set_value('project_type', project.agriculture_project_type || null);
            frm.set_value('planned_quantity', project.project_quantity || null);
            frm.set_value('planned_quantity_unit', project.project_unit || null);
            frm.set_value('planned_start_date', project.expected_start_date || null);
            frm.set_value('planned_end_date', project.expected_end_date || null);
        });
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
