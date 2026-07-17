frappe.ui.form.on("Project", {
    setup(frm) {
        frm.set_query("agriculture_project_type", () => ({filters: {is_active: 1}}));
        configure_queries(frm);
    },
    refresh(frm) {
        set_project_guidance(frm);
        add_farm_operation_actions(frm);
        return load_managed_context(frm, false);
    },
    async agriculture_project_type(frm) {
        await frm.set_value("managed_crop_animal_species", null);
        await frm.set_value("animal_breed", null);
        return load_managed_context(frm, true);
    },
    managed_crop_animal_species(frm) {
        frm.set_value("animal_breed", null);
        set_expected_output_item(frm);
        configure_queries(frm);
    },
});

function set_project_guidance(frm) {
    if (frm.is_new() && !frm.doc.agriculture_project_type) {
        frm.set_intro(
            __("For a farm operation, begin with Agriculture Project Type. The crop or animal, Farm, planning quantity, UOM, output Item, and Biological Asset will then be linked automatically."),
            "blue"
        );
    } else if (!frm.doc.agriculture_project_type) {
        frm.set_intro(
            __("This is a general ERPNext Project and cannot be used for crop or animal transactions. Select an Agriculture Project Type and complete the Agriculture Details section first."),
            "orange"
        );
    }
}

function add_farm_operation_actions(frm) {
    if (frm.is_new() || !frm.doc.agriculture_project_type) {
        return;
    }
    const context = {
        project: frm.doc.name,
        farm: frm.doc.farm,
    };
    frm.add_custom_button(__("Record Farm Activity"), () => {
        frappe.new_doc("Farm Activity", context);
    }, __("Farm Operations"));
    frm.add_custom_button(__("Plan Inputs and Resources"), () => {
        frappe.new_doc("Farm BOM", {
            ...context,
            project_type: frm.doc.agriculture_project_type,
            planned_quantity: frm.doc.project_quantity,
            planned_quantity_unit: frm.doc.project_unit,
            planned_start_date: frm.doc.expected_start_date,
            planned_end_date: frm.doc.expected_end_date,
        });
    }, __("Planning"));

    if (frm.doc.managed_item_doctype === "Crop Type") {
        frm.add_custom_button(__("Record Field Work"), () => {
            frappe.new_doc("Field Management", context);
        }, __("Farm Operations"));
        frm.add_custom_button(__("Harvest Crop"), () => {
            frappe.new_doc("Harvest Log", context);
        }, __("Farm Operations"));
    } else if (frm.doc.managed_item_doctype === "Livestock Species") {
        frm.add_custom_button(__("Record Animal Movement"), () => {
            frappe.new_doc("Animal Stock Entry", context);
        }, __("Farm Operations"));
    }

    if (frm.doc.biological_asset) {
        frm.add_custom_button(__("View Biological Asset"), () => {
            frappe.set_route("Form", "Biological Asset", frm.doc.biological_asset);
        }, __("IAS 41"));
        frm.add_custom_button(__("Record Valuation"), () => {
            frappe.new_doc("Biological Asset Valuation", {
                biological_asset: frm.doc.biological_asset,
            });
        }, __("IAS 41"));
    }
}

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
    frm._output_items = context.output_items || {};

    await frm.set_value("agriculture_farm_type", context.farm_type || null);
    await frm.set_value("managed_item_doctype", context.doctype || null);
    if (use_default && context.default_project_unit) {
        await frm.set_value("project_unit", context.default_project_unit);
    }
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
    await set_expected_output_item(frm);
}

async function set_expected_output_item(frm) {
    const managed_item = frm.doc.managed_crop_animal_species;
    await frm.set_value(
        "expected_output_item",
        managed_item ? (frm._output_items || {})[managed_item] || null : null
    );
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
