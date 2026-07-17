frappe.ui.form.on("Project", {
    setup(frm) {
        frm.set_query("agriculture_project_type", () => ({filters: {is_active: 1}}));
        configure_queries(frm);
    },
    refresh(frm) {
        return load_managed_context(frm, false);
    },
    async agriculture_project_type(frm) {
        await frm.set_value("managed_crop_animal_species", null);
        await frm.set_value("animal_breed", null);
        return load_managed_context(frm, true);
    },
    managed_crop_animal_species(frm) {
        frm.set_value("animal_breed", null);
        configure_queries(frm);
    },
});

async function load_managed_context(frm, use_default) {
    if (!frm.doc.agriculture_project_type) {
        frm._managed_produce_options = [];
        await frm.set_value("agriculture_farm_type", null);
        await frm.set_value("managed_item_doctype", null);
        configure_queries(frm);
        return;
    }

    const response = await frappe.call({
        method: "farm_management.farm_projects.agriculture_project.get_project_managed_item_context",
        args: {project_type: frm.doc.agriculture_project_type},
    });
    const context = response.message || {};
    const options = context.options || [];
    frm._managed_produce_options = options;

    await frm.set_value("agriculture_farm_type", context.farm_type || null);
    await frm.set_value("managed_item_doctype", context.doctype || null);
    configure_queries(frm);

    const current = frm.doc.managed_crop_animal_species;
    if (current && !options.includes(current)) {
        await frm.set_value("managed_crop_animal_species", null);
    }
    if (use_default && context.default) {
        await frm.set_value("managed_crop_animal_species", context.default);
    } else if (use_default && options.length === 1) {
        await frm.set_value("managed_crop_animal_species", options[0]);
    }
}

function configure_queries(frm) {
    const produce = frm._managed_produce_options?.length
        ? frm._managed_produce_options
        : ["__no_managed_produce__"];
    frm.set_query("managed_crop_animal_species", () => ({
        filters: {name: ["in", produce]},
    }));
    frm.set_query("animal_breed", () => ({
        filters: frm.doc.managed_crop_animal_species
            ? {species: frm.doc.managed_crop_animal_species, is_active: 1}
            : {name: "__no_breed__", is_active: 1},
    }));
}
