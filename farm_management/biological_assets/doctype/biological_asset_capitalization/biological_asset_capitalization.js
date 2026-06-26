frappe.ui.form.on('Biological Asset Capitalization', {
    refresh: function(frm) {
        if (frm.doc.docstatus === 0 && frm.doc.biological_asset) {
            frm.add_custom_button(__('Calculate Capitalization Amount'), function() {
                frappe.call({
                    method: 'farm_management.biological_assets.doctype.biological_asset_capitalization.biological_asset_capitalization.calculate_amount',
                    args: {
                        docname: frm.doc.name,
                        asset: frm.doc.biological_asset
                    },
                    callback: function(r) {
                        if (r.message) {
                            frm.set_value('amount', r.message);
                            frappe.show_alert({message: __('Amount Calculated from recent logs'), indicator: 'green'});
                        } else {
                            frappe.show_alert({message: __('No new logs found to capitalize'), indicator: 'orange'});
                        }
                    }
                });
            });
        }
    }
});
