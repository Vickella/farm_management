frappe.ui.form.on("Fish Batch", {
    setup(frm) {
        frm.set_query("species", () => ({
            filters: {species_group: "Aquaculture", is_active: 1},
        }));
    },
});
