frappe.ui.form.on('Livestock Health Event', {
    animal(frm) {
        if (!frm.doc.animal) {
            return;
        }
        frappe.db.get_value('Livestock Individual', frm.doc.animal, ['farm', 'biological_asset']).then((r) => {
            const animal = r.message || {};
            if (animal.farm) {
                frm.set_value('farm', animal.farm);
            }
            if (animal.biological_asset) {
                frm.set_value('biological_asset', animal.biological_asset);
            }
        });
    },
    product_used(frm) {
        if (!frm.doc.product_used) {
            return;
        }
        frappe.db.get_value('Item', frm.doc.product_used, 'valuation_rate').then((r) => {
            if (r.message && r.message.valuation_rate != null) {
                frm.set_value('cost', flt(r.message.valuation_rate));
            }
        });
    }
});