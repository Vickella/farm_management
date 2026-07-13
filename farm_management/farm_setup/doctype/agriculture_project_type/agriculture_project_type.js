frappe.ui.form.on("Agriculture Project Type", {
    refresh(frm) {
        set_managed_item_options(frm);
    },
    farm_type(frm) {
        frm.set_value("managed_item", null);
        set_managed_item_options(frm);
    },
});

function set_managed_item_options(frm) {
    if (!frm.doc.farm_type) {
        frm.set_df_property("managed_item", "options", "");
        return;
    }
    frappe.call({
        method: "farm_management.farm_projects.agriculture_project.get_managed_item_options",
        args: {farm_type: frm.doc.farm_type},
    }).then((response) => {
        frm.set_df_property(
            "managed_item",
            "options",
            ["", ...(response.message || [])].join("\n")
        );
    });
}
