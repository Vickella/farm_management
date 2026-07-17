frappe.ui.form.on("Farm Type", {
    setup(frm) {
        frm.set_query("farm_produce", "managed_items", (doc, cdt, cdn) => {
            const row = frappe.get_doc(cdt, cdn);
            const group = {
                "Animal Husbandry": "Livestock",
                "Poultry Production": "Poultry",
                "Apiculture": "Other",
            }[row.farm_activity];
            return group ? {filters: {species_group: group, is_active: 1}} : {};
        });
    },
});

frappe.ui.form.on("Farm Type Managed Item", {
    farm_activity(frm, cdt, cdn) {
        const row = frappe.get_doc(cdt, cdn);
        const master = ["Crop Production", "Agroforestry"].includes(row.farm_activity)
            ? "Crop Type"
            : "Livestock Species";
        frappe.model.set_value(cdt, cdn, "farm_produce", null);
        frappe.model.set_value(cdt, cdn, "farm_produce_doctype", master);
    },
});
