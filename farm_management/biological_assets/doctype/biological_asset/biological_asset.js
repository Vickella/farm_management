frappe.ui.form.on("Biological Asset", {
    setup: function(frm) {
        frm.set_query("linked_project", function() {
            return {
                filters: {
                    status: "Open"
                }
            };
        });
        frm.set_query("output_item", () => ({
            filters: {is_stock_item: 1, disabled: 0},
        }));
    },
    farm_type: function(frm) {
        set_managed_item_options(frm);
    },
    linked_project(frm) {
        if (!frm.doc.linked_project) {
            return;
        }
        frappe.db.get_value(
            "Project",
            frm.doc.linked_project,
            [
                "farm",
                "agriculture_farm_type",
                "managed_crop_animal_species",
                "expected_output_item",
                "animal_breed",
                "project_quantity",
                "project_unit",
                "initial_asset_cost",
                "expected_start_date",
            ]
        ).then((r) => {
            const project = r.message || {};
            frm.set_value("farm", project.farm || null);
            frm.set_value("farm_type", project.agriculture_farm_type || null);
            frm.set_value("managed_item", project.managed_crop_animal_species || null);
            frm.set_value("output_item", project.expected_output_item || null);
            frm.set_value("livestock_breed", project.animal_breed || null);
            frm.set_value("quantity", project.project_quantity || null);
            frm.set_value("unit", project.project_unit || null);
            frm.set_value("initial_cost", project.initial_asset_cost || 0);
            frm.set_value("acquisition_date", project.expected_start_date || null);
        });
    },
    managed_item: function(frm) {
        frm.set_value("livestock_breed", null);
        set_breed_query(frm);
    },
    refresh: function(frm) {
        set_managed_item_options(frm);
        set_breed_query(frm);
    }
});

function set_managed_item_options(frm) {
    if (frm.doc.farm_type) {
        frappe.model.with_doc("Farm Type", frm.doc.farm_type, function() {
            let farm_type = frappe.get_doc("Farm Type", frm.doc.farm_type);
            let options = [];
            if (farm_type && farm_type.managed_items) {
                farm_type.managed_items.forEach(function(row) {
                    if (row.farm_produce) {
                        options.push(row.farm_produce);
                    }
                });
            }
            frm.set_df_property("managed_item", "options", ["", ...options].join("\n"));
        });
    } else {
        frm.set_df_property("managed_item", "options", "");
    }
}

function set_breed_query(frm) {
    frm.set_query("livestock_breed", () => ({
        filters: frm.doc.managed_item
            ? {species: frm.doc.managed_item, is_active: 1}
            : {is_active: 1},
    }));
}
