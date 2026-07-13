frappe.ui.form.on("Greenhouse Cycle", {
    setup(frm) {
        frm.set_query("crop", () => ({}));
    },
});
