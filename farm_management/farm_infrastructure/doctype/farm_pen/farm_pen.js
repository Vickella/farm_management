frappe.ui.form.on("Farm Pen", {
    setup(frm) {
        frm.set_query("managed_species", () => ({
            filters: {species_group: "Livestock", is_active: 1},
        }));
    },
});
