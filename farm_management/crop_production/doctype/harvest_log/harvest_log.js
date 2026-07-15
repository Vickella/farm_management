frappe.ui.form.on("Harvest Log", {
    project(frm) {
        if (!frm.doc.project) {
            return;
        }
        frappe.db.get_value("Project", frm.doc.project, ["farm", "biological_asset"]).then((r) => {
            const project = r.message || {};
            frm.set_value("farm", project.farm || null);
            frm.set_value("biological_asset", project.biological_asset || null);
        });
    },
    conversion_item(frm) {
        if (!frm.doc.conversion_item) {
            frm.set_value("harvest_uom", null);
            return;
        }
        frappe.db.get_value("Item", frm.doc.conversion_item, "stock_uom").then((r) => {
            frm.set_value("harvest_uom", (r.message || {}).stock_uom || null);
        });
    },
});
