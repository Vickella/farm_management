frappe.ui.form.on('Harvest Transaction', {
    biological_asset(frm) {
        if (!frm.doc.biological_asset) {
            return;
        }
        frappe.db.get_value('Biological Asset', frm.doc.biological_asset, ['farm', 'quantity', 'net_fair_value', 'asset_category']).then((r) => {
            const asset = r.message || {};
            if (asset.farm) {
                frm.set_value('farm', asset.farm);
            }
            if (asset.quantity != null) {
                frm.set_value('asset_quantity_before', flt(asset.quantity));
                update_harvest_impact(frm, asset.asset_category);
            }
        });
    },
    farm(frm) {
        if (!frm.doc.farm) {
            return;
        }
        frappe.db.get_value('Farm', frm.doc.farm, 'owner_name').then((r) => {
            if (r.message && r.message.owner_name) {
                frm.set_value('company', r.message.owner_name);
            }
        });
    },
    quantity_harvested(frm) {
        update_harvest_impact(frm);
    },
    conversion_item(frm) {
        if (!frm.doc.conversion_item) {
            return;
        }
        frappe.db.get_value('Item', frm.doc.conversion_item, 'stock_uom').then((r) => {
            if (r.message && r.message.stock_uom) {
                frm.set_value('unit', r.message.stock_uom);
            }
        });
    }
});

function update_harvest_impact(frm) {
    const before = flt(frm.doc.asset_quantity_before);
    frappe.db.get_value('Biological Asset', frm.doc.biological_asset, 'asset_category').then((r) => {
        const category = (r.message || {}).asset_category;
        frm.set_value(
            'asset_quantity_after',
            category === 'Crops in Growth' ? 0 : before - flt(frm.doc.quantity_harvested)
        );
    });
}
