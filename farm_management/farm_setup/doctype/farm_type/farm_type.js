frappe.ui.form.on("Farm Type Managed Item", {
    managed_item_type(frm, cdt, cdn) {
        frappe.model.set_value(cdt, cdn, "crop_type", null);
        frappe.model.set_value(cdt, cdn, "livestock_species", null);
        frappe.model.set_value(cdt, cdn, "other_managed_item_name", null);
        frappe.model.set_value(cdt, cdn, "managed_item_name", null);
    },
    crop_type(frm, cdt, cdn) {
        const row = frappe.get_doc(cdt, cdn);
        frappe.model.set_value(cdt, cdn, "managed_item_name", row.crop_type || null);
    },
    livestock_species(frm, cdt, cdn) {
        const row = frappe.get_doc(cdt, cdn);
        frappe.model.set_value(cdt, cdn, "managed_item_name", row.livestock_species || null);
    },
    other_managed_item_name(frm, cdt, cdn) {
        const row = frappe.get_doc(cdt, cdn);
        frappe.model.set_value(cdt, cdn, "managed_item_name", row.other_managed_item_name || null);
    },
});
