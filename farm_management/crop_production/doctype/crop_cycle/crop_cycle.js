frappe.ui.form.on("Crop Cycle", {
    setup(frm) {
        frm.set_query("crop_variety", () => ({}));
    },
});
