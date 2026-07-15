frappe.ui.form.on("Project", {
    setup(frm) {
        frm.set_query("agriculture_project_type", () => ({filters: {is_active: 1}}));
    },
    refresh(frm) {
        configure_managed_item(frm);
        configure_breed_query(frm);
    },
    agriculture_project_type(frm) {
        if (!frm.doc.agriculture_project_type) {
            frm.set_value("agriculture_farm_type", null);
            frm.set_value("managed_crop_animal_species", null);
            configure_managed_item(frm);
            return;
        }
        frappe.db.get_value(
            "Agriculture Project Type",
            frm.doc.agriculture_project_type,
            ["farm_type", "managed_item"]
        ).then((response) => {
            const profile = response.message || {};
            frm.set_value("agriculture_farm_type", profile.farm_type || null);
            frm.set_value("managed_crop_animal_species", profile.managed_item || null);
            configure_managed_item(frm);
            configure_breed_query(frm);
        });
    },
    agriculture_farm_type(frm) {
        configure_managed_item(frm);
    },
    managed_crop_animal_species(frm) {
        frm.set_value("animal_breed", null);
        configure_breed_query(frm);
    },
});

function configure_managed_item(frm) {
    const farmType = frm.doc.agriculture_farm_type;
    if (!farmType) {
        frm.set_df_property("managed_crop_animal_species", "options", "");
        return;
    }
    frappe.call({
        method: "farm_management.farm_projects.agriculture_project.get_managed_item_options",
        args: {farm_type: farmType},
    }).then((response) => {
        frm.set_df_property(
            "managed_crop_animal_species",
            "options",
            ["", ...(response.message || [])].join("\n")
        );
    });
}

function configure_breed_query(frm) {
    frm.set_query("animal_breed", () => ({
        filters: frm.doc.managed_crop_animal_species
            ? {species: frm.doc.managed_crop_animal_species, is_active: 1}
            : {is_active: 1},
    }));
}
