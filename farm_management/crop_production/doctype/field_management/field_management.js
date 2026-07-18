frappe.ui.form.on("Field Management", {
    setup(frm) {
        frm.set_query("project", () => ({
            filters: {status: "Open", managed_item_doctype: "Crop Type"},
        }));
        frm.set_query("item", "requirements", () => ({
            filters: {disabled: 0},
        }));
    },
    project(frm) {
        if (!frm.doc.project) {
            return;
        }
        frappe.db.get_value("Project", frm.doc.project, "farm").then((r) => {
            frm.set_value("farm", (r.message || {}).farm || null);
        });
    },
});

frappe.ui.form.on("Field Management Requirement", {
    item(frm, cdt, cdn) {
        const row = frappe.get_doc(cdt, cdn);
        if (!row.item) {
            return;
        }
        frappe.db.get_value("Item", row.item, ["stock_uom", "valuation_rate"]).then((r) => {
            const item = r.message || {};
            frappe.model.set_value(cdt, cdn, "uom", item.stock_uom || null);
            frappe.model.set_value(cdt, cdn, "valuation_rate", flt(item.valuation_rate));
            calculate_requirements(frm);
        });
    },
    quantity: calculate_requirements,
    valuation_rate: calculate_requirements,
    requirements_remove: calculate_requirements,
});

function calculate_requirements(frm) {
    let total = 0;
    (frm.doc.requirements || []).forEach((row) => {
        const amount = flt(row.quantity) * flt(row.valuation_rate);
        frappe.model.set_value(row.doctype, row.name, "estimated_amount", amount);
        total += amount;
    });
    frm.set_value("total_estimated_cost", total);
}
