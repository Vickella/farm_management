frappe.ui.form.on('Contract Farming Agreement', {
    refresh(frm) {
        calculate_contract_input_total(frm);
    },
    production_target(frm) {
        calculate_expected_purchase(frm);
    },
    agreed_purchase_price_per_unit(frm) {
        calculate_expected_purchase(frm);
    }
});

frappe.ui.form.on('Input Loan Disbursement', {
    refresh(frm) {
        calculate_disbursement_total(frm);
    }
});

frappe.ui.form.on('Contract Farming Input', {
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
                frappe.model.set_value(cdt, cdn, 'unit_cost', flt(item.valuation_rate));
            }
            calculate_contract_input_row(frm, cdt, cdn);
        });
    },
    quantity(frm, cdt, cdn) {
        calculate_contract_input_row(frm, cdt, cdn);
    },
    unit_cost(frm, cdt, cdn) {
        calculate_contract_input_row(frm, cdt, cdn);
    },
    value(frm) {
        calculate_contract_input_total(frm);
        calculate_disbursement_total(frm);
    },
    inputs_provided_remove(frm) {
        calculate_contract_input_total(frm);
    },
    disbursed_inputs_remove(frm) {
        calculate_disbursement_total(frm);
    }
});

function calculate_contract_input_row(frm, cdt, cdn) {
    const row = frappe.get_doc(cdt, cdn);
    if (flt(row.quantity) && flt(row.unit_cost)) {
        frappe.model.set_value(cdt, cdn, 'value', flt(row.quantity) * flt(row.unit_cost));
    }
    calculate_contract_input_total(frm);
    calculate_disbursement_total(frm);
}

function calculate_contract_input_total(frm) {
    if (!frm.doc.inputs_provided) {
        return;
    }
    const total = frm.doc.inputs_provided.reduce((sum, row) => sum + flt(row.value), 0);
    frm.set_value('total_input_loan', total);
    calculate_expected_purchase(frm);
}

function calculate_disbursement_total(frm) {
    if (!frm.doc.disbursed_inputs) {
        return;
    }
    const total = frm.doc.disbursed_inputs.reduce((sum, row) => sum + flt(row.value), 0);
    frm.set_value('total_value', total);
}

function calculate_expected_purchase(frm) {
    if (!frm.doc.production_target && !frm.doc.agreed_purchase_price_per_unit) {
        return;
    }
    frm.set_value('total_expected_purchase', flt(frm.doc.production_target) * flt(frm.doc.agreed_purchase_price_per_unit));
}