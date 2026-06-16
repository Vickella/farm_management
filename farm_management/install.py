import json
from pathlib import Path

import frappe


FIXTURE_UNIQUE_FIELDS = {
    "Farm BOM": "bom_title",
    "Custom Field": ("dt", "fieldname"),
}

FIXTURE_LOAD_ORDER = [
    "farm_type.json",
    "crop_type.json",
    "farm_activity_type.json",
    "pest.json",
    "animal_disease.json",
    "farm_bom.json",
    "custom_field.json",
]

LEGACY_DOCTYPES = [
    "Agri AI Farm Management Settings Legacy",
]

WORKSPACE_GROUPS = [
    (
        "Farm Setup",
        [
            ("Farm", "DocType"),
            ("Farm Type", "DocType"),
            ("Crop Type", "DocType"),
            ("Farm Management Settings", "DocType"),
        ],
    ),
    (
        "Farm Infrastructure",
        [
            ("Farm Field", "DocType"),
            ("Farm Pond", "DocType"),
            ("Farm Pen", "DocType"),
            ("Fowl Run", "DocType"),
        ],
    ),
    ("Biological Assets", [("Biological Asset", "DocType"), ("Harvest Transaction", "DocType")]),
    (
        "Disease and Pest Intelligence",
        [("Disease Incident", "DocType"), ("Pest", "DocType"), ("Animal Disease", "DocType")],
    ),
    ("Farm BOM and Budgeting", [("Farm BOM", "DocType"), ("Farm Budget", "DocType")]),
    (
        "Contract Farming",
        [
            ("Outgrower Farmer", "DocType"),
            ("Contract Farming Agreement", "DocType"),
            ("Input Loan Disbursement", "DocType"),
            ("Harvest Recovery", "DocType"),
        ],
    ),
    ("Farm Calendar", [("Farm Activity", "DocType"), ("Farm Activity Type", "DocType")]),
    ("Reports", [("Farm KPI Summary", "Report"), ("Farm Budget Variance Analysis", "Report")]),
]

WORKSPACE_SHORTCUTS = [
    "Farm",
    "Biological Asset",
    "Disease Incident",
    "Farm BOM",
    "Farm Budget",
    "Contract Farming Agreement",
]


def get_workspace_content():
    content = [{"id": "farm-shortcuts-header", "type": "header", "data": {"text": "Shortcuts", "col": 12}}]

    content.extend(
        {
            "id": f"shortcut-{shortcut.lower().replace(' ', '-')}",
            "type": "shortcut",
            "data": {"shortcut_name": shortcut, "col": 3},
        }
        for shortcut in WORKSPACE_SHORTCUTS
    )

    content.extend(
        [
            {"id": "farm-spacer", "type": "spacer", "data": {"col": 12}},
            {
                "id": "farm-management-header",
                "type": "header",
                "data": {"text": "Farm Management", "col": 12},
            },
        ]
    )

    content.extend(
        {
            "id": f"card-{group.lower().replace(' ', '-').replace('&', 'and')}",
            "type": "card",
            "data": {"card_name": group, "col": 4},
        }
        for group, links in WORKSPACE_GROUPS
        if links
    )

    return content


def after_install():
    create_roles()
    remove_legacy_doctypes()
    seed_fixture_data()
    create_farm_workspace()
    setup_farm_management_settings()
    frappe.db.commit()
    print("farm_management: installation complete.")


def create_roles():
    for role in ["Farm Manager", "Farm Worker", "Agronomist"]:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role}).insert(ignore_permissions=True)


def remove_legacy_doctypes():
    for doctype in LEGACY_DOCTYPES:
        if frappe.db.exists("DocType", doctype):
            frappe.delete_doc("DocType", doctype, force=True, ignore_permissions=True)


def setup_farm_management_settings():
    if not frappe.db.exists("Farm Management Settings", "Farm Management Settings"):
        doc = frappe.new_doc("Farm Management Settings")
        doc.enable_ai_assistant = 1
        doc.enable_auto_activity_generation = 1
        doc.enable_fair_value_scheduler = 1
        doc.insert(ignore_permissions=True)


def seed_fixture_data():
    fixtures_dir = Path(frappe.get_app_path("farm_management")).parent / "fixtures"
    if not fixtures_dir.exists():
        return

    fixture_paths = sorted(fixtures_dir.glob("*.json"), key=get_fixture_sort_key)
    for fixture_path in fixture_paths:
        with fixture_path.open(encoding="utf-8") as fixture_file:
            records = json.load(fixture_file)

        for record in records:
            if fixture_record_exists(record):
                continue

            try:
                frappe.get_doc(record).insert(ignore_permissions=True, ignore_if_duplicate=True)
            except frappe.DuplicateEntryError:
                continue


def get_fixture_sort_key(fixture_path):
    try:
        return FIXTURE_LOAD_ORDER.index(fixture_path.name)
    except ValueError:
        return len(FIXTURE_LOAD_ORDER)


def fixture_record_exists(record):
    doctype = record.get("doctype")
    if not doctype:
        return False

    if record.get("name") and frappe.db.exists(doctype, record.get("name")):
        return True

    unique_field = FIXTURE_UNIQUE_FIELDS.get(doctype)
    if isinstance(unique_field, str) and record.get(unique_field):
        return frappe.db.exists(doctype, {unique_field: record.get(unique_field)})

    if isinstance(unique_field, tuple) and all(record.get(fieldname) for fieldname in unique_field):
        return frappe.db.exists(
            doctype,
            {fieldname: record.get(fieldname) for fieldname in unique_field},
        )

    meta = frappe.get_meta(doctype)
    if meta.autoname and meta.autoname.startswith("field:"):
        fieldname = meta.autoname.split(":", 1)[1]
        if record.get(fieldname):
            return frappe.db.exists(doctype, record.get(fieldname))

    return False


def create_farm_workspace():
    if frappe.db.exists("Workspace", "Farm Management"):
        ws = frappe.get_doc("Workspace", "Farm Management")
    else:
        ws = frappe.new_doc("Workspace")
        ws.name = "Farm Management"

    ws.name = "Farm Management"
    ws.label = "Farm Management"
    ws.title = "Farm Management"
    ws.category = "Modules"
    ws.icon = "agriculture"
    ws.is_standard = 1
    ws.module = "Farm Setup"
    ws.public = 1
    ws.is_hidden = 0
    ws.sequence_id = 99
    ws.for_user = ""
    ws.parent_page = ""
    ws.restrict_to_domain = ""
    ws.indicator_color = ""

    ws.links = []
    ws.shortcuts = []
    ws.charts = []
    ws.number_cards = []
    ws.quick_lists = []
    ws.roles = []
    ws.custom_blocks = []

    ws.content = json.dumps(get_workspace_content())

    for doctype in WORKSPACE_SHORTCUTS:
        ws.append(
            "shortcuts",
            {
                "label": doctype,
                "type": "DocType",
                "link_to": doctype,
                "doc_view": "List",
                "color": "Grey",
            },
        )

    for label, links in WORKSPACE_GROUPS:
        ws.append(
            "links",
            {
                "type": "Card Break",
                "label": label,
                "link_count": len(links),
                "link_type": "DocType",
                "is_query_report": 0,
                "hidden": 0,
                "onboard": 0,
            },
        )
        for link, link_type in links:
            ws.append(
                "links",
                {
                    "dependencies": "" if link_type == "DocType" else link,
                    "type": "Link",
                    "label": link,
                    "link_type": link_type,
                    "link_to": link,
                    "link_count": 0,
                    "is_query_report": 1 if link_type == "Report" else 0,
                    "hidden": 0,
                    "onboard": 0,
                },
            )

    if ws.is_new():
        ws.insert(ignore_permissions=True)
    else:
        ws.save(ignore_permissions=True)
