frappe.ui.form.on("Farm Pond", {
    setup(frm) {
        frm.set_query("managed_species", () => ({
            filters: {species_group: "Aquaculture", is_active: 1},
        }));
    },
});
