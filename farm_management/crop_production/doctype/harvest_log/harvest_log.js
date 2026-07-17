frappe.ui.form.on("Harvest Log", {
    setup(frm) {
        frm.set_query("project", () => ({
            filters: {
                status: "Open",
                managed_item_doctype: "Crop Type",
                biological_asset: ["is", "set"],
            },
        }));
        frm.set_query("target_warehouse", () => ({
            filters: {is_group: 0, disabled: 0},
        }));
    },
    refresh(frm) {
        update_valuation_rate(frm);
    },
    project(frm) {
        if (!frm.doc.project) {
            return;
        }
        frappe.db.get_value("Project", frm.doc.project, ["farm", "biological_asset", "expected_output_item"]).then((r) => {
            const project = r.message || {};
            frm.set_value("farm", project.farm || null);
            frm.set_value("biological_asset", project.biological_asset || null);
            frm.set_value("conversion_item", project.expected_output_item || null);
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
    harvested_quantity: update_valuation_rate,
    harvest_fair_value: update_valuation_rate,
});

function update_valuation_rate(frm) {
    const quantity = flt(frm.doc.harvested_quantity);
    frm.set_value(
        "valuation_rate",
        quantity ? flt(frm.doc.harvest_fair_value) / quantity : 0
    );
}
