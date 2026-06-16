app_name = "farm_management"
app_title = "Farm Management"
app_publisher = "VerityCore Consultancy"
app_description = "Enterprise Agricultural ERP extending ERPNext"
app_version = "0.0.1"
app_icon = "octicon octicon-file-directory"
app_color = "green"
app_email = "dev@veritycore.co.zw"
app_license = "MIT"

after_install = "farm_management.install.after_install"

fixtures = [
    {"dt": "Custom Field", "filters": [["module", "=", "Farm Management"]]},
    {"dt": "Property Setter", "filters": [["module", "=", "Farm Management"]]},
    {"dt": "Role", "filters": [["name", "in", ["Farm Manager", "Farm Worker", "Agronomist"]]]},
    {"dt": "Workspace", "filters": [["name", "=", "Farm Management"]]},
]

doc_events = {
    "Project": {
        "validate": "farm_management.farm_projects.agriculture_project.validate_agriculture_project",
    }
}

scheduler_events = {
    "daily": [
        "farm_management.biological_assets.doctype.biological_asset.biological_asset.update_fair_values",
        "farm_management.farm_calendar.doctype.farm_activity.farm_activity.generate_scheduled_tasks",
    ]
}
