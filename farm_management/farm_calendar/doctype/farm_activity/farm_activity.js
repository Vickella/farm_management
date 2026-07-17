frappe.ui.form.on("Farm Activity", {
    setup(frm) {
        frm.set_query("project", () => ({
            filters: {status: "Open", farm: frm.doc.farm || undefined},
        }));
        frm.set_query("activity_type", () => ({filters: {is_active: 1}}));
        frm.set_query("biological_asset", () => ({
            filters: {
                farm: frm.doc.farm || undefined,
                linked_project: frm.doc.project || undefined,
                status: "Active",
            },
        }));
    },
    project(frm) {
        if (!frm.doc.project) {
            return;
        }
        frappe.db.get_value("Project", frm.doc.project, ["farm", "biological_asset"]).then((r) => {
            const project = r.message || {};
            frm.set_value("farm", project.farm || null);
            if (frm.doc.capitalizable) {
                frm.set_value("biological_asset", project.biological_asset || null);
            }
        });
    },
    activity_type(frm) {
        if (!frm.doc.activity_type) {
            return;
        }
        frappe.db.get_value("Farm Activity Type", frm.doc.activity_type, "activity_name").then((r) => {
            if (!frm.doc.activity_title) {
                frm.set_value("activity_title", (r.message || {}).activity_name || null);
            }
        });
    },
    capitalizable(frm) {
        if (frm.doc.capitalizable && frm.doc.project) {
            frm.trigger("project");
        }
    },
});
