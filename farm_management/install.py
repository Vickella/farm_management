import json
from pathlib import Path

import frappe
from frappe.utils import flt


FIXTURE_UNIQUE_FIELDS = {
    "Farm BOM": "bom_title",
    "Custom Field": ("dt", "fieldname"),
    "Farm Type": "farm_type_name",
    "Crop Type": "crop_name",
}

FIXTURE_LOAD_ORDER = [
    "farm_type.json",
    "crop_type.json",
    "farm_activity_type.json",
    "pest.json",
    "animal_disease.json",
    "custom_field.json",
]

# Farm BOMs are operational templates with site-specific Project, Item, and
# UOM links. They must never be installed as global master data.
EXCLUDED_INSTALL_FIXTURES = {"farm_bom.json"}

LEGACY_DOCTYPES = [
    "Agri AI Farm Management Settings Legacy",
    "Farm Pond",
    "Fish Batch",
    "Pond Management",
    "Water Quality Log",
    "Fish Feeding Log",
    "Feeding Log",
    "Animal Herd",
    "Breeding Log",
    "Cattle Herd",
    "Cattle Infrastructure",
    "Meat Production Log",
    "Contract Farming Agreement",
    "Contract Farming Input",
    "Harvest Recovery",
    "Input Loan Disbursement",
    "Outgrower Farmer",
    "Crop Cycle",
    "Dairy Cow Herd",
    "Dairy Infrastructure",
    "Dairy Milking Cycle",
    "Lactation Cycle",
    "Milk Yield Log",
    "Goat Breeding Log",
    "Goat Herd",
    "Goat Meat Milk Log",
    "Climate Control Log",
    "Greenhouse Cycle",
    "Greenhouse Harvest Log",
    "Farrowing Log",
    "Pig Batch",
    "Pig Infrastructure",
    "Broiler Batch",
    "Egg Production Log",
    "Poultry Flock",
    "Poultry Infrastructure",
    "Budget Forecasting",
    "Budget Forecasting Expense",
    "Standard Cost Calculation BOM",
    "Standard Cost Calculation BOM Item",
]

LEGACY_MODULES = [
    "Agri Ai",
    "Animal Husbandry",
    "Contract Farming",
    "Dairy Production",
    "Fish Farming",
    "Goat Farming",
    "Greenhouse Farming",
    "Pig Farming",
    "Poultry Production",
]

LEGACY_PAGES = ["agri-gpt", "farm-weather"]
LEGACY_REPORTS = ["Contract Farming Statement"]

LEGACY_PROJECT_CUSTOM_FIELDS = [
    "Project-breed",
    "Project-initial_quantity",
    "Project-crop_variety",
    "Project-planting_date",
    "Project-expected_yield",
    "Project-harvest_date",
    "Project-field_allocation",
    "Project-fertilizer_schedule",
    "Project-poultry_breed",
    "Project-chick_quantity",
    "Project-growth_period_days",
    "Project-mortality_target_percent",
    "Project-vaccination_schedule",
    "Project-feed_program",
    "Project-fowl_run_allocation",
    "Project-fish_species",
    "Project-fish_species_managed_item",
    "Project-fingerling_quantity",
    "Project-stocking_date",
    "Project-feed_type",
    "Project-water_monitoring_schedule",
    "Project-pond_allocation",
    "Project-fish_harvest_date",
    "Project-dairy_breed",
    "Project-herd_size",
    "Project-daily_yield_target_litres",
    "Project-pen_allocation_dairy",
    "Project-goat_breed",
    "Project-goat_herd_size",
    "Project-kidding_season",
    "Project-pen_allocation_goats",
    "Project-pig_breed",
    "Project-pig_herd_size",
    "Project-farrowing_date",
    "Project-pen_allocation_pigs",
    "Project-greenhouse_crop",
    "Project-greenhouse_area_sqm",
    "Project-planting_date_gh",
    "Project-harvest_date_gh",
]

WORKSPACE_GROUPS = [
    (
        "Farm Setup",
        [
            ("Farm", "DocType"),
            ("Farm Type", "DocType"),
            ("Agriculture Project Type", "DocType"),
            ("Crop Type", "DocType"),
            ("Project", "DocType"),
            ("Farm Management Settings", "DocType"),
        ],
    ),
    (
        "Field Operations",
        [
            ("Farm Field", "DocType"),
            ("Field Management", "DocType"),
            ("Farm Activity Type", "DocType"),
            ("Farm Activity", "DocType"),
            ("Harvest Log", "DocType"),
        ],
    ),
    (
        "Farm Infrastructure",
        [
            ("Farm Pen", "DocType"),
            ("Fowl Run", "DocType"),
        ],
    ),
    (
        "Livestock Records",
        [
            ("Animal Stock Entry", "DocType"),
            ("Livestock Individual", "DocType"),
            ("Livestock Species", "DocType"),
            ("Livestock Breed", "DocType"),
            ("Livestock Health Event", "DocType"),
            ("Livestock Breeding Record", "DocType"),
        ],
    ),
    (
        "IAS 41 Biological Assets",
        [
            ("Biological Asset", "DocType"),
            ("Biological Asset Capitalization", "DocType"),
            ("Biological Asset Valuation", "DocType"),
            ("Harvest Transaction", "DocType"),
            ("Biological Asset Register", "Report"),
            ("Biological Asset GL Reconciliation", "Report"),
            ("Animal Stock Ledger", "Report"),
        ],
    ),
    (
        "Disease and Pest Intelligence",
        [("Disease Incident", "DocType"), ("Animal Disease", "DocType"), ("Pest", "DocType")],
    ),
    (
        "Planning and Costing",
        [
            ("Farm BOM", "DocType"),
            ("Farm Budget", "DocType"),
            ("Farm Budget Variance Analysis", "Report"),
        ],
    ),
    (
        "Farm Accounting",
        [
            ("Farm Cashbook", "DocType"),
            ("Profit and Loss Statement", "Report"),
            ("Accounts Receivable Summary", "Report"),
            ("Accounts Payable Summary", "Report"),
            ("General Ledger", "Report"),
            ("Farm KPI Summary", "Report"),
        ],
    ),
]

WORKSPACE_SHORTCUTS = [
    "Farm",
    "Project",
    "Biological Asset",
    "Farm Activity",
    "Harvest Log",
    "Animal Stock Entry",
    "Farm Cashbook",
    ("Farm KPI Summary", "Report"),
    ("Profit and Loss Statement", "Report"),
]

def get_workspace_content():
    content = [{"id": "farm-shortcuts-header", "type": "header", "data": {"text": "Shortcuts", "col": 12}}]

    content.extend(
        {
            "id": f"shortcut-{get_shortcut_label(shortcut).lower().replace(' ', '-')}",
            "type": "shortcut",
            "data": {"shortcut_name": get_shortcut_label(shortcut), "col": 3},
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


def get_shortcut_label(shortcut):
    if isinstance(shortcut, tuple):
        return shortcut[0]
    return shortcut


def after_install():
    create_roles()
    remove_legacy_doctypes()
    apply_phase2_updates()
    frappe.db.commit()
    print("farm_management: installation complete.")


def apply_phase2_updates():
    ensure_erpnext_dependency()
    migrate_harvest_quantity_field()
    remove_legacy_project_custom_fields()
    remove_legacy_doctypes()
    retire_removed_fish_masters()
    ensure_module_defs()
    ensure_amendable_doctypes()
    seed_agricultural_uoms()
    seed_erpnext_operational_masters()
    normalize_managed_item_master_links()
    seed_fixture_data()
    retire_legacy_flat_farm_types()
    normalize_existing_farm_type_links()
    seed_missing_crop_types()
    seed_livestock_breeds()
    seed_agriculture_project_types()
    seed_pests()
    seed_animal_diseases()
    setup_farm_management_settings()
    setup_biological_asset_accounts()
    setup_biological_asset_sales_accounts()
    create_farm_workspace()


def ensure_erpnext_dependency():
    missing = [
        doctype
        for doctype in ("Company", "Project", "Item", "UOM", "Account")
        if not frappe.db.exists("DocType", doctype)
    ]
    if missing:
        frappe.throw(
            "Farm Management requires ERPNext before migration. Missing DocTypes: "
            + ", ".join(missing)
        )


def migrate_harvest_quantity_field():
    table = "tabHarvest Log"
    if not frappe.db.table_exists(table):
        return
    if not frappe.db.has_column(table, "total_yield_tons"):
        return
    if not frappe.db.has_column(table, "harvested_quantity"):
        return
    frappe.db.sql(
        f"""update `{table}`
        set harvested_quantity = total_yield_tons
        where ifnull(harvested_quantity, 0) = 0
          and ifnull(total_yield_tons, 0) != 0"""
    )


def seed_agricultural_uoms():
    whole_number_uoms = {"Head", "Bird", "Colony"}
    for uom_name in (
        "Head",
        "Bird",
        "Colony",
        "Hectare",
        "Kg",
        "Tonne",
        "Bag",
        "Crate",
        "Litre",
    ):
        if frappe.db.exists("UOM", uom_name):
            continue
        uom = frappe.new_doc("UOM")
        uom.uom_name = uom_name
        uom.must_be_whole_number = uom_name in whole_number_uoms
        uom.insert(ignore_permissions=True)


def seed_erpnext_operational_masters():
    # ERPNext uses this master while creating a Company's default transit
    # warehouse. Older/partial sites can be missing it and then fail both
    # company creation and Frappe's integration-test setup.
    if frappe.db.exists("DocType", "Warehouse Type") and not frappe.db.exists(
        "Warehouse Type", "Transit"
    ):
        frappe.get_doc(
            {"doctype": "Warehouse Type", "name": "Transit"}
        ).insert(ignore_permissions=True)


def ensure_module_defs():
    app_path = Path(frappe.get_app_path("farm_management"))
    modules_path = app_path / "modules.txt"
    if not modules_path.exists():
        modules_path = app_path.parent / "modules.txt"

    if not modules_path.exists():
        frappe.throw(f"Could not find modules.txt for farm_management at {app_path}")

    module_names = [
        module_name.strip()
        for module_name in modules_path.read_text(encoding="utf-8").splitlines()
        if module_name.strip()
    ]
    for module_name in module_names:
        if not frappe.db.exists("Module Def", module_name):
            frappe.get_doc(
                {
                    "doctype": "Module Def",
                    "module_name": module_name,
                    "app_name": "farm_management",
                }
            ).insert(ignore_permissions=True)

def ensure_amendable_doctypes():
    from frappe.custom.doctype.custom_field.custom_field import create_custom_field

    app_path = Path(frappe.get_app_path("farm_management"))
    modules_path = app_path / "modules.txt"
    if not modules_path.exists():
        modules_path = app_path.parent / "modules.txt"
    app_modules = [
        module.strip()
        for module in modules_path.read_text(encoding="utf-8").splitlines()
        if module.strip()
    ]
    doctypes = frappe.get_all(
        "DocType",
        filters={"module": ["in", app_modules], "is_submittable": 1, "istable": 0},
        pluck="name",
    )
    for doctype in doctypes:
        if not frappe.get_meta(doctype).has_field("amended_from"):
            create_custom_field(
                doctype,
                {
                    "fieldname": "amended_from",
                    "label": "Amended From",
                    "fieldtype": "Link",
                    "options": doctype,
                    "read_only": 1,
                    "no_copy": 1,
                    "print_hide": 1,
                    "insert_after": "naming_series",
                    "module": "Farm Management",
                },
                ignore_validate=True,
            )
        for permission in frappe.get_all(
            "DocPerm",
            filters={"parent": doctype, "cancel": 1, "amend": 0},
            pluck="name",
        ):
            frappe.db.set_value("DocPerm", permission, "amend", 1, update_modified=False)


def create_roles():
    for role in ["Farm Manager", "Farm Worker", "Agronomist"]:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role}).insert(ignore_permissions=True)


def remove_legacy_doctypes():
    for doctype in LEGACY_DOCTYPES:
        if frappe.db.exists("DocType", doctype):
            frappe.delete_doc("DocType", doctype, force=True, ignore_permissions=True)
    for report in LEGACY_REPORTS:
        if frappe.db.exists("Report", report):
            frappe.delete_doc("Report", report, force=True, ignore_permissions=True)
    for page in LEGACY_PAGES:
        if frappe.db.exists("Page", page):
            frappe.delete_doc("Page", page, force=True, ignore_permissions=True)
    for module in LEGACY_MODULES:
        if frappe.db.exists("Module Def", module):
            frappe.delete_doc("Module Def", module, force=True, ignore_permissions=True)


def retire_removed_fish_masters():
    for project_type in ("Fish Farming", "Tilapia Production", "Catfish Production"):
        if frappe.db.exists("Agriculture Project Type", project_type):
            frappe.db.set_value(
                "Agriculture Project Type",
                project_type,
                "is_active",
                0,
                update_modified=False,
            )
    for species in ("Tilapia", "Catfish", "Trout", "Shrimp"):
        if frappe.db.exists("Livestock Species", species):
            frappe.db.set_value(
                "Livestock Species",
                species,
                "is_active",
                0,
                update_modified=False,
            )
    if frappe.db.exists("Farm Type", "Aquaculture"):
        frappe.db.set_value(
            "Farm Type",
            "Aquaculture",
            "is_active",
            0,
            update_modified=False,
        )
    for activity in frappe.get_all(
        "Farm Activity Type",
        filters={"activity_name": ["like", "Aquaculture - %"]},
        pluck="name",
    ):
        frappe.db.set_value(
            "Farm Activity Type",
            activity,
            "is_active",
            0,
            update_modified=False,
        )


def remove_legacy_project_custom_fields():
    for custom_field in LEGACY_PROJECT_CUSTOM_FIELDS:
        if frappe.db.exists("Custom Field", custom_field):
            frappe.delete_doc("Custom Field", custom_field, force=True, ignore_permissions=True)


def setup_farm_management_settings():
    if not frappe.db.exists("Farm Management Settings", "Farm Management Settings"):
        doc = frappe.new_doc("Farm Management Settings")
        doc.enable_auto_activity_generation = 1
        doc.enable_fair_value_scheduler = 1
        doc.insert(ignore_permissions=True)


def setup_biological_asset_accounts():
    settings = frappe.get_single("Farm Management Settings")
    company = settings.default_company or frappe.defaults.get_user_default("Company") or frappe.db.get_single_value(
        "Global Defaults", "default_company"
    )
    if not company:
        return

    biological_assets_group = ensure_account(
        "Biological Assets",
        company,
        root_type="Asset",
        report_type="Balance Sheet",
        is_group=1,
    )
    cwip_account = ensure_account(
        "Biological Asset Capital Work In Progress",
        company,
        root_type="Asset",
        report_type="Balance Sheet",
        parent_account=biological_assets_group,
        account_type="Capital Work in Progress",
    )

    default_asset_account = None
    for farm_type in frappe.get_all("Farm Type", filters={"is_active": 1}, pluck="name"):
        account = ensure_account(
            f"Biological Asset - {farm_type}",
            company,
            root_type="Asset",
            report_type="Balance Sheet",
            parent_account=biological_assets_group,
            account_type="Fixed Asset",
        )
        if not default_asset_account:
            default_asset_account = account
        setup_managed_item_accounts(farm_type, company, biological_assets_group, cwip_account, gain_loss_account=None)

    gain_loss_account = ensure_account(
        "Biological Asset Fair Value Gain Loss",
        company,
        root_type="Expense",
        report_type="Profit and Loss",
        account_type="Expense Account",
    )
    for farm_type in frappe.get_all("Farm Type", filters={"is_active": 1}, pluck="name"):
        setup_managed_item_accounts(farm_type, company, biological_assets_group, cwip_account, gain_loss_account)

    updates = {}
    if not settings.default_company:
        updates["default_company"] = company
    if updates:
        frappe.db.set_value("Farm Management Settings", "Farm Management Settings", updates, update_modified=False)


def setup_biological_asset_sales_accounts(company=None):
    settings = frappe.get_single("Farm Management Settings")
    company = company or settings.default_company or frappe.defaults.get_user_default("Company") or frappe.db.get_single_value(
        "Global Defaults", "default_company"
    )
    if not company:
        return

    ensure_account(
        "Biological Asset Sales Receivable",
        company,
        root_type="Asset",
        report_type="Balance Sheet",
    )
    ensure_account(
        "Biological Asset Sales Income",
        company,
        root_type="Income",
        report_type="Profit and Loss",
    )
    ensure_account(
        "Biological Asset Cost of Sales",
        company,
        root_type="Expense",
        report_type="Profit and Loss",
        account_type="Cost of Goods Sold",
    )


def setup_managed_item_accounts(farm_type_name, company, biological_assets_group, cwip_account, gain_loss_account):
    farm_type = frappe.get_doc("Farm Type", farm_type_name)
    changed = False
    for row in farm_type.get("managed_items", []):
        if not row.farm_produce:
            continue

        asset_account = ensure_account(
            f"Biological Asset - {row.farm_produce}",
            company,
            root_type="Asset",
            report_type="Balance Sheet",
            parent_account=biological_assets_group,
            account_type="Fixed Asset",
        )
        if asset_account and not row.biological_asset_account:
            row.biological_asset_account = asset_account
            changed = True
        if cwip_account and not row.capital_work_in_progress_account:
            row.capital_work_in_progress_account = cwip_account
            changed = True
        if gain_loss_account and not row.fair_value_gain_loss_account:
            row.fair_value_gain_loss_account = gain_loss_account
            changed = True

    if changed:
        farm_type.save(ignore_permissions=True)


def ensure_account(
    account_name,
    company,
    root_type,
    report_type,
    parent_account=None,
    account_type=None,
    is_group=0,
):
    existing = frappe.db.get_value("Account", {"account_name": account_name, "company": company}, "name")
    if existing:
        return existing

    if not parent_account:
        parent_account = get_root_account(company, root_type)
        if not parent_account:
            return None

    account = frappe.new_doc("Account")
    account.account_name = account_name
    account.company = company
    account.parent_account = parent_account
    account.root_type = root_type
    account.report_type = report_type
    account.is_group = is_group
    if account_type:
        account.account_type = account_type
    account.insert(ignore_permissions=True)
    return account.name


def get_root_account(company, root_type):
    return frappe.db.get_value(
        "Account",
        {
            "company": company,
            "root_type": root_type,
            "is_group": 1,
            "parent_account": ["is", "not set"],
        },
        "name",
    ) or frappe.db.get_value(
        "Account",
        {
            "company": company,
            "root_type": root_type,
            "is_group": 1,
        },
        "name",
    )


def seed_fixture_data():
    fixtures_dir = Path(frappe.get_app_path("farm_management")).parent / "fixtures"
    if not fixtures_dir.exists():
        return

    fixture_paths = sorted(fixtures_dir.glob("*.json"), key=get_fixture_sort_key)
    for fixture_path in fixture_paths:
        if fixture_path.name in EXCLUDED_INSTALL_FIXTURES:
            continue
        with fixture_path.open(encoding="utf-8") as fixture_file:
            records = json.load(fixture_file)

        for record in records:
            if record.get("doctype") == "Farm Type":
                record = normalize_farm_type_fixture(record)
            doctype = record.get("doctype")
            if not doctype or not frappe.db.exists("DocType", doctype):
                frappe.log_error(
                    title="Farm Management fixture skipped",
                    message=f"Skipped {fixture_path.name}: DocType {doctype or '<missing>'} is unavailable.",
                )
                continue
            if is_legacy_project_custom_field(record):
                continue

            existing_name = get_fixture_existing_name(record)
            if existing_name:
                update_existing_fixture_record(record, existing_name)
                continue

            try:
                frappe.get_doc(record).insert(ignore_permissions=True, ignore_if_duplicate=True)
            except frappe.DuplicateEntryError:
                continue


def normalize_farm_type_fixture(record):
    activity_map = {
        "Crop": ("Crop Production", "Crop Type"),
        "Animal Species": ("Animal Husbandry", "Livestock Species"),
        "Poultry": ("Poultry Production", "Livestock Species"),
        "Apiary": ("Apiculture", "Livestock Species"),
        "Other": ("Agroforestry", "Crop Type"),
    }
    normalized = dict(record)
    normalized.pop("category", None)
    normalized["managed_items"] = []
    for row in record.get("managed_items", []):
        activity, master = activity_map.get(row.get("managed_item_type"), ("Crop Production", "Crop Type"))
        normalized["managed_items"].append(
            {
                "doctype": "Farm Type Managed Item",
                "farm_activity": activity,
                "farm_produce_doctype": master,
                "farm_produce": row.get("managed_item_name"),
            }
        )
    return normalized


def is_legacy_project_custom_field(record):
    if record.get("doctype") != "Custom Field" or record.get("dt") != "Project":
        return False
    name = record.get("name") or f"Project-{record.get('fieldname')}"
    return name in LEGACY_PROJECT_CUSTOM_FIELDS


def seed_agriculture_project_types():
    for ambiguous_type in ("Poultry Production", "Mixed Farming"):
        if frappe.db.exists("Agriculture Project Type", ambiguous_type):
            frappe.db.set_value(
                "Agriculture Project Type",
                ambiguous_type,
                "is_active",
                0,
                update_modified=False,
            )
    project_types = [
        ("Crop Production", "Crop Production", None),
        ("Horticulture", "Horticulture", None),
        ("Greenhouse Farming", "Horticulture", None),
        ("Broiler Production", "Poultry", "Broilers"),
        ("Layer Production", "Poultry", "Layers"),
        ("Road Runner Production", "Poultry", "Road Runners"),
        ("Animal Husbandry", "Animal Husbandry", None),
        ("Cattle Ranching", "Animal Husbandry", "Cattle"),
        ("Cattle Pen Fattening", "Animal Husbandry", "Cattle"),
        ("Dairy Production", "Animal Husbandry", "Cattle"),
        ("Goat Farming", "Animal Husbandry", "Goats"),
        ("Sheep Farming", "Animal Husbandry", "Sheep"),
        ("Pig Farming", "Animal Husbandry", "Pigs"),
        ("Rabbit Production", "Animal Husbandry", "Rabbits"),
        ("Apiculture", "Apiculture", "Honey Bees"),
        ("Agroforestry", "Agroforestry", None),
    ]
    for project_type_name, farm_type, managed_item in project_types:
        if not frappe.db.exists("Farm Type", farm_type):
            continue
        if frappe.db.exists("Agriculture Project Type", project_type_name):
            continue
        doc = frappe.new_doc("Agriculture Project Type")
        doc.project_type_name = project_type_name
        doc.farm_type = farm_type
        doc.managed_item = managed_item
        doc.is_active = 1
        doc.insert(ignore_permissions=True)


def get_fixture_sort_key(fixture_path):
    try:
        return FIXTURE_LOAD_ORDER.index(fixture_path.name)
    except ValueError:
        return len(FIXTURE_LOAD_ORDER)


def fixture_record_exists(record):
    return bool(get_fixture_existing_name(record))


def get_fixture_existing_name(record):
    doctype = record.get("doctype")
    if not doctype:
        return None

    if record.get("name") and frappe.db.exists(doctype, record.get("name")):
        return record.get("name")

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

    return None


def update_existing_fixture_record(record, existing_name):
    doctype = record.get("doctype")
    # Reference masters become user-owned after installation. Never overwrite
    # Farm Types, Crop Types, BOMs, pests, or diseases during later migrations.
    if doctype != "Custom Field":
        return

    force_update_custom_field_type(record, existing_name)

    doc = frappe.get_doc(doctype, existing_name)
    for key, value in record.items():
        if key == "doctype":
            continue
        if isinstance(value, list):
            doc.set(key, [])
            for row in value:
                row = row.copy()
                row.pop("doctype", None)
                doc.append(key, row)
        else:
            doc.set(key, value)
    doc.save(ignore_permissions=True)


def force_update_custom_field_type(record, existing_name):
    new_fieldtype = record.get("fieldtype")
    if not new_fieldtype:
        return

    current_fieldtype = frappe.db.get_value("Custom Field", existing_name, "fieldtype")
    if current_fieldtype == new_fieldtype:
        return

    updates = {"fieldtype": new_fieldtype}
    if record.get("options") is not None:
        updates["options"] = record.get("options")
    frappe.db.set_value("Custom Field", existing_name, updates, update_modified=False)
    if record.get("dt"):
        frappe.clear_cache(doctype=record.get("dt"))


def retire_legacy_flat_farm_types():
    legacy_names = [
        "Maize",
        "Wheat",
        "Soybeans",
        "Tobacco",
        "Cotton",
        "Sugar Beans",
        "Groundnuts",
        "Tomatoes",
        "Potatoes",
        "Onions",
        "Cabbage",
        "Peppers",
        "Flowers",
        "Greenhouse Farming",
        "Cattle",
        "Goats",
        "Sheep",
        "Pigs",
        "Rabbits",
        "Broilers",
        "Layers",
        "Road Runners",
        "Turkey",
        "Ducks",
    ]
    for name in legacy_names:
        if frappe.db.exists("Farm Type", name):
            frappe.db.set_value(
                "Farm Type",
                name,
                {
                    "is_active": 0,
                    "description": f"Legacy managed item retained for historical links. Use a broad Farm Type with managed item rows instead of {name}.",
                },
            )


def normalize_existing_farm_type_links():
    crop_items = {
        "Maize",
        "Wheat",
        "Soybeans",
        "Tobacco",
        "Cotton",
        "Sugar Beans",
        "Groundnuts",
    }
    horticulture_items = {"Tomatoes", "Potatoes", "Onions", "Cabbage", "Peppers", "Flowers", "Greenhouse Farming"}
    livestock_items = {"Cattle", "Goats", "Sheep", "Pigs", "Rabbits"}
    poultry_items = {"Broilers", "Layers", "Road Runners", "Turkey", "Ducks"}

    def broad_type(old_value):
        if old_value in crop_items:
            return "Crop Production"
        if old_value in horticulture_items:
            return "Horticulture"
        if old_value in livestock_items:
            return "Animal Husbandry"
        if old_value in poultry_items:
            return "Poultry"
        return old_value

    for name, farm_type in frappe.get_all(
        "Biological Asset",
        fields=["name", "farm_type"],
        filters={"farm_type": ["in", list(crop_items | horticulture_items | livestock_items | poultry_items)]},
        as_list=True,
    ):
        frappe.db.set_value(
            "Biological Asset",
            name,
            {"farm_type": broad_type(farm_type), "managed_item": farm_type},
            update_modified=False,
        )

    for doctype, link_field in (("Farm Pen", "animal_type"), ("Fowl Run", "bird_type")):
        for name, farm_type in frappe.get_all(
            doctype,
            fields=["name", link_field],
            filters={link_field: ["in", list(livestock_items | poultry_items)]},
            as_list=True,
        ):
            frappe.db.set_value(
                doctype,
                name,
                {link_field: broad_type(farm_type), "managed_species": farm_type},
                update_modified=False,
            )

    for farm in frappe.get_all("Farm", pluck="name"):
        doc = frappe.get_doc("Farm", farm)
        changed = False
        selected = []
        for row in doc.get("farm_type", []):
            value = broad_type(row.farm_type)
            if value not in selected:
                selected.append(value)
            if value != row.farm_type:
                changed = True
        if changed:
            doc.set("farm_type", [])
            for value in selected:
                doc.append("farm_type", {"farm_type": value})
            doc.save(ignore_permissions=True)


def seed_livestock_breeds():
    species_rows = [
        ("Cattle", "Animal Husbandry", "Livestock", ["Brahman", "Bonsmara", "Tuli", "Mashona", "Holstein Friesian"]),
        ("Goats", "Animal Husbandry", "Livestock", ["Boer", "Kalahari Red", "Matabele", "Mashona"]),
        ("Sheep", "Animal Husbandry", "Livestock", ["Dorper", "Merino", "Damara"]),
        ("Pigs", "Animal Husbandry", "Livestock", ["Large White", "Landrace", "Duroc"]),
        ("Rabbits", "Animal Husbandry", "Livestock", ["New Zealand White", "Californian"]),
        ("Broilers", "Poultry", "Poultry", ["Ross 308", "Cobb 500", "Arbor Acres"]),
        ("Layers", "Poultry", "Poultry", ["Hy-Line Brown", "Lohmann Brown", "ISA Brown"]),
        ("Road Runners", "Poultry", "Poultry", []),
        ("Turkey", "Poultry", "Poultry", []),
        ("Ducks", "Poultry", "Poultry", []),
        ("Honey Bees", "Apiculture", "Other", []),
        ("Bee Colonies", "Apiculture", "Other", []),
    ]
    for species_name, farm_type, species_group, breeds in species_rows:
        if not frappe.db.exists("Livestock Species", species_name):
            doc = frappe.new_doc("Livestock Species")
            doc.species_name = species_name
            doc.farm_type = farm_type if frappe.db.exists("Farm Type", farm_type) else None
            doc.species_group = species_group
            doc.is_active = 1
            doc.insert(ignore_permissions=True)
        for breed_name in breeds:
            if not frappe.db.exists("Livestock Breed", breed_name):
                breed = frappe.new_doc("Livestock Breed")
                breed.breed_name = breed_name
                breed.species = species_name
                breed.is_active = 1
                breed.insert(ignore_permissions=True)


def seed_missing_crop_types():
    crop_categories = {
        "Sugar Beans": "Crop Production",
        "Groundnuts": "Crop Production",
        "Onions": "Horticulture",
        "Cabbage": "Horticulture",
        "Peppers": "Horticulture",
        "Flowers": "Horticulture",
        "Greenhouse Vegetables": "Horticulture",
        "Fruit Trees": "Agroforestry",
        "Woodlots": "Agroforestry",
    }
    for crop_name, category in crop_categories.items():
        if frappe.db.exists("Crop Type", crop_name):
            continue
        crop = frappe.new_doc("Crop Type")
        crop.crop_name = crop_name
        crop.category = category if frappe.db.exists("Farm Type", category) else None
        crop.insert(ignore_permissions=True)


def normalize_managed_item_master_links():
    table = "tabFarm Type Managed Item"
    if not frappe.db.table_exists(table) or not frappe.db.has_column(table, "farm_produce"):
        return
    if not frappe.db.has_column(table, "managed_item_name"):
        return
    activity_sql = (
        "case managed_item_type "
        "when 'Crop' then 'Crop Production' "
        "when 'Animal Species' then 'Animal Husbandry' "
        "when 'Poultry' then 'Poultry Production' "
        "when 'Apiary' then 'Apiculture' "
        "else 'Agroforestry' end"
    )
    master_sql = (
        "case when managed_item_type in ('Crop', 'Other') "
        "then 'Crop Type' else 'Livestock Species' end"
    )
    frappe.db.sql(
        f"""update `{table}`
        set farm_activity = ifnull(nullif(farm_activity, ''), {activity_sql}),
            farm_produce_doctype = ifnull(nullif(farm_produce_doctype, ''), {master_sql}),
            farm_produce = ifnull(nullif(farm_produce, ''), managed_item_name)
        where ifnull(farm_produce, '') = ''"""
    )


def seed_pests():
    pests = [
        {
            "pest_name": "Fall Armyworm",
            "scientific_name": "Spodoptera frugiperda",
            "pest_type": "Insect",
            "affects": "Crops",
            "severity_level": "High",
            "signs_and_symptoms": "Ragged leaf feeding, windowing on young leaves, frass in whorls, dead-heart in young maize, and larvae hidden in leaf whorls.",
            "causes": "Infestation by migratory fall armyworm moth larvae, especially during warm humid periods and late scouting.",
            "recommended_treatment": "Scout early, hand destroy egg masses where practical, protect natural enemies, and treat whorls when threshold is reached.",
            "chemical_treatment": "Use locally registered products such as emamectin benzoate, chlorantraniliprole, or spinosad according to label directions.",
            "organic_treatment": "Apply Bt products on small larvae, neem-based sprays, ash/sand whorl treatment, and field sanitation.",
        },
        {
            "pest_name": "Aphids",
            "scientific_name": "Aphidoidea",
            "pest_type": "Insect",
            "affects": "Crops",
            "severity_level": "High",
            "signs_and_symptoms": "Clusters of soft-bodied insects on tender shoots, curled leaves, sticky honeydew, sooty mould, stunting, and virus symptoms.",
            "causes": "Rapid aphid multiplication in warm conditions, nitrogen-rich soft growth, and low predator populations.",
            "recommended_treatment": "Monitor leaf undersides, conserve ladybirds and lacewings, remove heavily infested shoots, and manage nitrogen.",
            "chemical_treatment": "Use registered systemic or contact aphicides only when thresholds are exceeded.",
            "organic_treatment": "Use insecticidal soap, neem oil, strong water sprays, and habitat for beneficial insects.",
        },
        {
            "pest_name": "Bollworm",
            "scientific_name": "Helicoverpa armigera",
            "pest_type": "Insect",
            "affects": "Crops",
            "severity_level": "High",
            "signs_and_symptoms": "Bored fruit, damaged flower buds, feeding holes, frass around entry points, and larvae inside pods or bolls.",
            "causes": "Egg laying by bollworm moths during flowering and fruiting periods.",
            "recommended_treatment": "Scout flowers and fruit, remove infested plant parts, rotate crops, and apply treatment to young larvae.",
            "chemical_treatment": "Use registered selective insecticides and rotate modes of action to avoid resistance.",
            "organic_treatment": "Use Bt, pheromone traps, trap crops, and encourage parasitoids.",
        },
        {
            "pest_name": "Stem Borer",
            "scientific_name": "Busseola fusca",
            "pest_type": "Insect",
            "affects": "Crops",
            "severity_level": "High",
            "signs_and_symptoms": "Pin holes on leaves, dead-heart symptoms, stem tunnelling, weak stems, lodging, and frass at entry holes.",
            "causes": "Larvae boring into maize or sorghum stems after egg hatch.",
            "recommended_treatment": "Plant early, destroy crop residues, scout young crops, and treat before larvae enter stems.",
            "chemical_treatment": "Apply registered granular or foliar insecticides targeted at whorls when larvae are small.",
            "organic_treatment": "Use push-pull systems, crop residue destruction, and biological controls where available.",
        },
        {
            "pest_name": "Whitefly",
            "scientific_name": "Bemisia tabaci",
            "pest_type": "Insect",
            "affects": "Crops",
            "severity_level": "High",
            "signs_and_symptoms": "White insects flying when disturbed, yellowing leaves, honeydew, sooty mould, stunting, and viral disease spread.",
            "causes": "Whitefly build-up in warm dry conditions and continuous host crops.",
            "recommended_treatment": "Remove weeds, use reflective mulch or netting, monitor sticky traps, and protect beneficial insects.",
            "chemical_treatment": "Use registered whitefly products with mode-of-action rotation.",
            "organic_treatment": "Use neem, insecticidal soap, yellow sticky traps, and crop hygiene.",
        },
        {
            "pest_name": "Red Spider Mite",
            "scientific_name": "Tetranychus urticae",
            "pest_type": "Insect",
            "affects": "Crops",
            "severity_level": "High",
            "signs_and_symptoms": "Fine webbing, leaf stippling, bronzing, yellowing, leaf drop, and tiny mites on leaf undersides.",
            "causes": "Hot dry conditions, dusty crops, and repeated broad-spectrum insecticide use.",
            "recommended_treatment": "Reduce dust stress, maintain irrigation, remove infested leaves, and protect predatory mites.",
            "chemical_treatment": "Use registered miticides and rotate active ingredients.",
            "organic_treatment": "Use wettable sulphur where crop-safe, neem, horticultural oils, and predatory mites.",
        },
        {
            "pest_name": "Cutworm",
            "scientific_name": "Agrotis spp.",
            "pest_type": "Insect",
            "affects": "Crops",
            "severity_level": "High",
            "signs_and_symptoms": "Seedlings cut at soil level, missing plants, larvae curled in soil near damaged seedlings.",
            "causes": "Nocturnal cutworm larvae feeding after weed growth or previous crop residues.",
            "recommended_treatment": "Prepare land early, remove weeds before planting, scout at night or early morning, and replant gaps.",
            "chemical_treatment": "Use registered bait or soil-applied insecticides where infestation is severe.",
            "organic_treatment": "Use collars around seedlings, hand-pick larvae, and maintain clean seedbeds.",
        },
        {
            "pest_name": "Thrips",
            "scientific_name": "Thysanoptera",
            "pest_type": "Insect",
            "affects": "Crops",
            "severity_level": "High",
            "signs_and_symptoms": "Silvery streaks, distorted young leaves, flower scarring, black specks, and virus transmission.",
            "causes": "Hot dry weather, flowering host crops, and poor field hygiene.",
            "recommended_treatment": "Use blue/yellow sticky traps, remove weeds, avoid water stress, and scout flowers and new growth.",
            "chemical_treatment": "Use registered thrip control products with resistance management.",
            "organic_treatment": "Use neem, spinosad where allowed, reflective mulch, and beneficial predatory bugs.",
        },
    ]
    for pest in pests:
        name = pest.get("pest_name")
        if not frappe.db.exists("Pest", name):
            frappe.get_doc({"doctype": "Pest", **pest}).insert(ignore_permissions=True)


def seed_animal_diseases():
    diseases = [
        {
            "disease_name": "Foot and Mouth Disease",
            "affects": "Cattle",
            "mortality_risk": "High",
            "is_notifiable": 1,
            "zoonotic_risk": 0,
            "vaccination_available": 1,
            "symptoms": "Fever, salivation, mouth blisters, lameness, reduced appetite, drop in milk yield, and reluctance to move.",
            "prevention_method": "Vaccination, movement control, quarantine, disinfection, and rapid reporting.",
            "vaccination_schedule": "Follow national veterinary authority schedule for risk areas.",
            "treatment": "No curative treatment. Provide supportive care, soft feed, clean water, wound care, and prevent secondary infections.",
        },
        {
            "disease_name": "Newcastle Disease",
            "affects": "Poultry",
            "mortality_risk": "Very High",
            "is_notifiable": 1,
            "zoonotic_risk": 0,
            "vaccination_available": 1,
            "symptoms": "Sudden deaths, greenish diarrhoea, coughing, sneezing, twisted necks, paralysis, and severe egg production drop.",
            "prevention_method": "Strict vaccination, biosecurity, isolation of new birds, and sanitation.",
            "vaccination_schedule": "Use LaSota or I-2 schedules recommended by a veterinarian.",
            "treatment": "No specific cure. Isolate affected birds, provide supportive care, and prevent secondary infections.",
        },
        {
            "disease_name": "Coccidiosis",
            "affects": "Poultry",
            "mortality_risk": "High",
            "is_notifiable": 0,
            "zoonotic_risk": 0,
            "vaccination_available": 1,
            "symptoms": "Bloody or watery diarrhoea, ruffled feathers, weight loss, depression, pale combs, and uneven growth.",
            "prevention_method": "Dry litter, proper stocking density, clean drinkers, and coccidiostat programme.",
            "vaccination_schedule": "Use poultry coccidiosis vaccine where appropriate.",
            "treatment": "Treat promptly with approved anticoccidials such as amprolium or sulphonamides as advised by a veterinarian.",
        },
        {
            "disease_name": "Mastitis",
            "affects": "Cattle",
            "mortality_risk": "Medium",
            "is_notifiable": 0,
            "zoonotic_risk": 0,
            "vaccination_available": 0,
            "symptoms": "Swollen hot udder, clots or watery milk, pain, fever, reduced milk production, and loss of appetite.",
            "prevention_method": "Clean milking routine, teat dipping, dry cow therapy, and culling chronic cases.",
            "vaccination_schedule": "",
            "treatment": "Use culture-guided intramammary antibiotics, anti-inflammatory therapy, frequent stripping, and veterinary care.",
        },
        {
            "disease_name": "Anthrax",
            "affects": "All Livestock",
            "mortality_risk": "Very High",
            "is_notifiable": 1,
            "zoonotic_risk": 1,
            "vaccination_available": 1,
            "symptoms": "Sudden death, bleeding from body openings, rapid bloating, fever, weakness, and collapse.",
            "prevention_method": "Annual vaccination in risk areas, avoid opening carcasses, safe carcass disposal, and quarantine.",
            "vaccination_schedule": "Annual vaccination before high-risk season where recommended.",
            "treatment": "Emergency veterinary response. Early antibiotics may help exposed animals, but carcasses must not be opened.",
        },
        {
            "disease_name": "African Swine Fever",
            "affects": "Pigs",
            "mortality_risk": "Very High",
            "is_notifiable": 1,
            "zoonotic_risk": 0,
            "vaccination_available": 0,
            "symptoms": "High fever, red or purple skin patches, weakness, vomiting, diarrhoea, abortions, and sudden death.",
            "prevention_method": "Strict biosecurity, no swill feeding, quarantine, control pig movement, and keep pigs away from wild suids.",
            "vaccination_schedule": "",
            "treatment": "No treatment. Report immediately, isolate, and follow veterinary authority instructions.",
        },
        {
            "disease_name": "Avian Influenza",
            "affects": "Poultry",
            "mortality_risk": "Very High",
            "is_notifiable": 1,
            "zoonotic_risk": 1,
            "vaccination_available": 0,
            "symptoms": "Sudden deaths, swollen head, respiratory distress, cyanosis of combs, diarrhoea, nervous signs, and sharp egg production drop.",
            "prevention_method": "Strict biosecurity, wild bird exclusion, movement control, quarantine, and immediate reporting.",
            "vaccination_schedule": "Use only under official veterinary disease-control programmes.",
            "treatment": "No routine treatment. Report suspected cases immediately and follow veterinary authority instructions.",
        },
        {
            "disease_name": "Lumpy Skin Disease",
            "affects": "Cattle",
            "mortality_risk": "Medium",
            "is_notifiable": 1,
            "zoonotic_risk": 0,
            "vaccination_available": 1,
            "symptoms": "Fever, firm skin nodules, swollen lymph nodes, lameness, reduced milk, eye/nasal discharge, and wounds.",
            "prevention_method": "Vaccination, biting insect control, quarantine, and sanitation.",
            "vaccination_schedule": "Annual vaccination before vector season in endemic areas.",
            "treatment": "Supportive care, wound cleaning, antibiotics for secondary infection, anti-inflammatory therapy, and fly control.",
        },
        {
            "disease_name": "Theileriosis (East Coast Fever)",
            "affects": "Cattle",
            "mortality_risk": "Very High",
            "is_notifiable": 0,
            "zoonotic_risk": 0,
            "vaccination_available": 0,
            "symptoms": "Fever, swollen lymph nodes, anaemia, difficulty breathing, weakness, jaundice, and death if untreated.",
            "prevention_method": "Strict tick control, dipping, pasture management, and early disease recognition.",
            "vaccination_schedule": "",
            "treatment": "Early treatment with buparvaquone or oxytetracycline where appropriate, plus fever control, fluids, nutrition, and tick removal.",
        },
    ]
    for disease in diseases:
        name = disease.get("disease_name")
        if not frappe.db.exists("Animal Disease", name):
            frappe.get_doc({"doctype": "Animal Disease", **disease}).insert(ignore_permissions=True)


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

    for shortcut in WORKSPACE_SHORTCUTS:
        if isinstance(shortcut, tuple) and len(shortcut) == 3:
            label, shortcut_type, link_to = shortcut
        elif isinstance(shortcut, tuple):
            label, shortcut_type = shortcut
            link_to = label
        else:
            label, shortcut_type, link_to = shortcut, "DocType", shortcut
        ws.append(
            "shortcuts",
            {
                "label": label,
                "type": shortcut_type,
                "link_to": link_to,
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
        for link_data in links:
            if len(link_data) == 3:
                link, link_type, link_to = link_data
            else:
                link, link_type = link_data
                link_to = link
            ws.append(
                "links",
                {
                    "dependencies": "" if link_type == "DocType" else link_to,
                    "type": "Link",
                    "label": link,
                    "link_type": link_type,
                    "link_to": link_to,
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


def verify_installation():
    expected_doctypes = [
        "Farm",
        "Farm Type",
        "Farm Type Managed Item",
        "Agriculture Project Type",
        "Crop Type",
        "Farm Management Settings",
        "Farm Field",
        "Farm Pen",
        "Fowl Run",
        "Field Management",
        "Field Management Requirement",
        "Harvest Log",
        "Livestock Species",
        "Livestock Breed",
        "Livestock Individual",
        "Animal Stock Entry",
        "Livestock Health Event",
        "Livestock Breeding Record",
        "Biological Asset",
        "Biological Asset Capitalization",
        "Biological Asset Valuation",
        "Harvest Transaction",
        "Disease Incident",
        "Pest",
        "Animal Disease",
        "Farm BOM",
        "Farm BOM Item",
        "Farm Budget",
        "Farm Budget Item",
        "Farm Cashbook",
        "Farm Cashbook Entry",
        "Farm Activity",
        "Farm Activity Type",
    ]
    expected_reports = [
        "Farm KPI Summary",
        "Farm Budget Variance Analysis",
        "Biological Asset Register",
        "Biological Asset GL Reconciliation",
        "Animal Stock Ledger",
    ]
    expected_account_names = [
        "Biological Assets",
        "Biological Asset Capital Work In Progress",
        "Biological Asset Fair Value Gain Loss",
        "Biological Asset Sales Receivable",
        "Biological Asset Sales Income",
        "Biological Asset Cost of Sales",
    ]
    legacy_project_fields = [
        fieldname.replace("Project-", "")
        for fieldname in LEGACY_PROJECT_CUSTOM_FIELDS
    ]

    missing_doctypes = [
        doctype for doctype in expected_doctypes if not frappe.db.exists("DocType", doctype)
    ]
    missing_reports = [
        report for report in expected_reports if not frappe.db.exists("Report", report)
    ]
    workspace_exists = bool(frappe.db.exists("Workspace", "Farm Management"))
    workspace_links = 0
    workspace_shortcuts = 0
    if workspace_exists:
        workspace = frappe.get_doc("Workspace", "Farm Management")
        workspace_links = len(workspace.get("links", []))
        workspace_shortcuts = len(workspace.get("shortcuts", []))

    remaining_legacy_project_fields = frappe.get_all(
        "Custom Field",
        filters={"dt": "Project", "fieldname": ["in", legacy_project_fields]},
        pluck="fieldname",
    )
    settings = frappe.get_single("Farm Management Settings")
    company = settings.default_company or frappe.defaults.get_user_default("Company") or frappe.db.get_single_value(
        "Global Defaults", "default_company"
    )
    missing_accounts = []
    if company:
        missing_accounts = [
            account_name
            for account_name in expected_account_names
            if not frappe.db.exists("Account", {"account_name": account_name, "company": company})
        ]

    return {
        "missing_doctypes": missing_doctypes,
        "missing_reports": missing_reports,
        "missing_accounts": missing_accounts,
        "workspace_exists": workspace_exists,
        "workspace_links": workspace_links,
        "workspace_shortcuts": workspace_shortcuts,
        "remaining_legacy_project_fields": remaining_legacy_project_fields,
    }
