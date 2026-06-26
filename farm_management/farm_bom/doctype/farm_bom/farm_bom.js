frappe.ui.form.on('Farm BOM', {
    setup: function(frm) {
        // Any setup logic
    }
});

frappe.ui.form.on('Farm BOM Item', {
    quantity: function(frm, cdt, cdn) {
        calculate_total(frm, cdt, cdn);
    },
    unit_cost: function(frm, cdt, cdn) {
        calculate_total(frm, cdt, cdn);
    }
});

function calculate_total(frm, cdt, cdn) {
    let row = frappe.get_doc(cdt, cdn);
    if (row.quantity && row.unit_cost) {
        frappe.model.set_value(cdt, cdn, 'total_cost', row.quantity * row.unit_cost);
    } else {
        frappe.model.set_value(cdt, cdn, 'total_cost', 0);
    }
    
    // Calculate total estimated cost
    let total = 0;
    if (frm.doc.ingredients) {
        frm.doc.ingredients.forEach(function(d) {
            total += flt(d.total_cost);
        });
    }
    frm.set_value('total_estimated_cost', total);
}
