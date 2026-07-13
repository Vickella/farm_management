frappe.ui.form.on("Biological Asset", {
    setup: function(frm) {
        frm.set_query("linked_project", function() {
            return {
                filters: {
                    status: "Open"
                }
            };
        });
    },
    farm_type: function(frm) {
        set_managed_item_options(frm);
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
                    if (row.managed_item_name && row.is_active) {
                        options.push(row.managed_item_name);
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
