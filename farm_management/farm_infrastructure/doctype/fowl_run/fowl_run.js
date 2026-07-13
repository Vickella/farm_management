frappe.ui.form.on("Fowl Run", {
    setup(frm) {
        frm.set_query("managed_species", () => ({
            filters: {species_group: "Poultry", is_active: 1},
        }));
    },
});
