frappe.ui.form.on("Cattle Herd", {
    setup(frm) {
        frm.set_query("breed", () => ({
            filters: {is_active: 1},
        }));
    },
});
