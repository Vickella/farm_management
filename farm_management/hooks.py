app_name = "farm_management"
app_title = "Farm Management"
app_publisher = "VerityCore Consultancy"
app_description = "Enterprise Agricultural ERP extending ERPNext"
app_version = "0.0.1"
app_icon = "octicon octicon-file-directory"
app_color = "green"
app_email = "dev@veritycore.co.zw"
app_license = "MIT"

# Farm Management links to ERPNext accounting, stock, project, UOM, Item, and
# company DocTypes throughout its schema. Declaring this dependency prevents
# installation or migration against a Frappe-only site.
required_apps = ["erpnext"]

after_install = "farm_management.install.after_install"
after_migrate = ["farm_management.install.apply_phase2_updates"]

doctype_js = {
    "Project": "public/js/project.js",
}

fixtures = [
    {"dt": "Custom Field", "filters": [["module", "=", "Farm Management"]]},
]

status_sync_events = {
    "on_submit": "farm_management.lifecycle.sync_status_on_submit",
    "on_cancel": "farm_management.lifecycle.sync_status_on_cancel",
}

doc_events = {
    doctype: status_sync_events
    for doctype in (
        "Animal Stock Entry",
        "Biological Asset Capitalization",
        "Biological Asset Valuation",
        "Farm Cashbook",
        "Field Management",
        "Harvest Log",
        "Harvest Transaction",
    )
}
doc_events.update({
    "Project": {
        "validate": "farm_management.farm_projects.agriculture_project.validate_agriculture_project",
        "after_insert": "farm_management.farm_projects.agriculture_project.sync_biological_asset_for_project",
        "on_update": "farm_management.farm_projects.agriculture_project.sync_biological_asset_for_project",
    },
    "Stock Entry": {
        "on_submit": "farm_management.biological_assets.valuation.sync_project_material_issue",
        "on_cancel": "farm_management.biological_assets.valuation.cancel_project_material_issue",
    }
})

scheduler_events = {
    "daily": [
        "farm_management.biological_assets.doctype.biological_asset.biological_asset.update_fair_values",
        "farm_management.farm_calendar.doctype.farm_activity.farm_activity.generate_scheduled_tasks",
    ]
}
