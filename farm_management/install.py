import json
from pathlib import Path

import frappe


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
    "farm_bom.json",
    "custom_field.json",
]

LEGACY_DOCTYPES = [
    "Agri AI Farm Management Settings Legacy",
]

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
            ("Farm Management Settings", "DocType"),
        ],
    ),
    (
        "Crop Production",
        [
            ("Crop Cycle", "DocType"),
            ("Field Management", "DocType"),
            ("Harvest Log", "DocType"),
            ("Farm Field", "DocType"),
        ],
    ),
    (
        "Greenhouse Farming",
        [
            ("Greenhouse Cycle", "DocType"),
            ("Climate Control Log", "DocType"),
            ("Greenhouse Harvest Log", "DocType"),
        ],
    ),
    (
        "Poultry Production",
        [
            ("Poultry Flock", "DocType"),
            ("Broiler Batch", "DocType"),
            ("Egg Production Log", "DocType"),
            ("Poultry Infrastructure", "DocType"),
            ("Fowl Run", "DocType"),
        ],
    ),
    (
        "Fish Farming",
        [
            ("Fish Batch", "DocType"),
            ("Pond Management", "DocType"),
            ("Water Quality Log", "DocType"),
            ("Fish Feeding Log", "DocType"),
            ("Feeding Log", "DocType"),
            ("Farm Pond", "DocType"),
        ],
    ),
    (
        "Animal Husbandry",
        [
            ("Animal Herd", "DocType"),
            ("Cattle Herd", "DocType"),
            ("Cattle Infrastructure", "DocType"),
            ("Breeding Log", "DocType"),
            ("Meat Production Log", "DocType"),
            ("Farm Pen", "DocType"),
        ],
    ),
    (
        "Dairy Production",
        [
            ("Dairy Cow Herd", "DocType"),
            ("Dairy Infrastructure", "DocType"),
            ("Lactation Cycle", "DocType"),
            ("Milk Yield Log", "DocType"),
            ("Dairy Milking Cycle", "DocType"),
        ],
    ),
    (
        "Goat Farming",
        [
            ("Goat Herd", "DocType"),
            ("Goat Breeding Log", "DocType"),
            ("Goat Meat Milk Log", "DocType"),
        ],
    ),
    (
        "Pig Farming",
        [
            ("Pig Batch", "DocType"),
            ("Farrowing Log", "DocType"),
            ("Pig Infrastructure", "DocType"),
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
            ("Animal Stock Ledger", "Report"),
        ],
    ),
    (
        "Disease and Pest Intelligence",
        [("Disease Incident", "DocType"), ("Animal Disease", "DocType"), ("Pest", "DocType")],
    ),
    (
        "Contract Farming",
        [
            ("Contract Farming Agreement", "DocType"),
            ("Outgrower Farmer", "DocType"),
            ("Input Loan Disbursement", "DocType"),
            ("Harvest Recovery", "DocType"),
            ("Contract Farming Statement", "Report"),
        ],
    ),
    (
        "Budgeting and Costing",
        [
            ("Farm Budget", "DocType"),
            ("Budget Forecasting", "DocType"),
            ("Farm BOM", "DocType"),
            ("Standard Cost Calculation BOM", "DocType"),
            ("Farm Budget Variance Analysis", "Report"),
        ],
    ),
    ("Accounting", [("Farm Cashbook", "DocType")]),
    (
        "Farm Calendar",
        [("Farm Activity", "DocType"), ("Farm Activity Type", "DocType")],
    ),
    (
        "Decision Support",
        [
            ("Farm KPI Summary", "Report"),
            ("Farm Weather Forecast", "Page", "farm-weather"),
            ("Agri GPT", "Page", "agri-gpt"),
        ],
    ),
]

WORKSPACE_SHORTCUTS = [
    "Farm",
    "Agriculture Project Type",
    "Crop Cycle",
    "Poultry Flock",
    "Fish Batch",
    "Animal Herd",
    "Animal Stock Entry",
    "Biological Asset",
    "Farm Budget",
    ("Farm KPI Summary", "Report"),
    ("Farm Weather", "Page", "farm-weather"),
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
    ensure_module_defs()
    remove_legacy_project_custom_fields()
    seed_fixture_data()
    seed_agriculture_project_types()
    retire_legacy_flat_farm_types()
    normalize_existing_farm_type_links()
    seed_livestock_breeds()
    seed_pests()
    seed_animal_diseases()
    setup_farm_management_settings()
    setup_biological_asset_accounts()
    setup_contract_farming_accounts()
    create_farm_workspace()


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

def create_roles():
    for role in ["Farm Manager", "Farm Worker", "Agronomist"]:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role}).insert(ignore_permissions=True)


def remove_legacy_doctypes():
    for doctype in LEGACY_DOCTYPES:
        if frappe.db.exists("DocType", doctype):
            frappe.delete_doc("DocType", doctype, force=True, ignore_permissions=True)


def remove_legacy_project_custom_fields():
    for custom_field in LEGACY_PROJECT_CUSTOM_FIELDS:
        if frappe.db.exists("Custom Field", custom_field):
            frappe.delete_doc("Custom Field", custom_field, force=True, ignore_permissions=True)


def setup_farm_management_settings():
    if not frappe.db.exists("Farm Management Settings", "Farm Management Settings"):
        doc = frappe.new_doc("Farm Management Settings")
        doc.enable_ai_assistant = 1
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


def setup_contract_farming_accounts():
    settings = frappe.get_single("Farm Management Settings")
    company = settings.default_company or frappe.defaults.get_user_default("Company") or frappe.db.get_single_value(
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
        "Contract Farming Input Loans Receivable",
        company,
        root_type="Asset",
        report_type="Balance Sheet",
    )
    ensure_account(
        "Contract Farming Input Clearing",
        company,
        root_type="Liability",
        report_type="Balance Sheet",
    )
    ensure_account(
        "Contract Farming Harvest Purchases",
        company,
        root_type="Expense",
        report_type="Profit and Loss",
    )
    ensure_account(
        "Contract Farming Grower Payable",
        company,
        root_type="Liability",
        report_type="Balance Sheet",
    )


def setup_managed_item_accounts(farm_type_name, company, biological_assets_group, cwip_account, gain_loss_account):
    farm_type = frappe.get_doc("Farm Type", farm_type_name)
    changed = False
    for row in farm_type.get("managed_items", []):
        if not row.managed_item_name:
            continue

        asset_account = ensure_account(
            f"Biological Asset - {row.managed_item_name}",
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
        with fixture_path.open(encoding="utf-8") as fixture_file:
            records = json.load(fixture_file)

        for record in records:
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


def is_legacy_project_custom_field(record):
    if record.get("doctype") != "Custom Field" or record.get("dt") != "Project":
        return False
    name = record.get("name") or f"Project-{record.get('fieldname')}"
    return name in LEGACY_PROJECT_CUSTOM_FIELDS


def seed_agriculture_project_types():
    project_types = [
        ("Crop Production", "Crop Production", None),
        ("Horticulture", "Horticulture", None),
        ("Greenhouse Farming", "Horticulture", None),
        ("Poultry Production", "Poultry", None),
        ("Broiler Production", "Poultry", "Broilers"),
        ("Layer Production", "Poultry", "Layers"),
        ("Animal Husbandry", "Animal Husbandry", None),
        ("Cattle Ranching", "Animal Husbandry", "Cattle"),
        ("Cattle Pen Fattening", "Animal Husbandry", "Cattle"),
        ("Dairy Production", "Animal Husbandry", "Cattle"),
        ("Goat Farming", "Animal Husbandry", "Goats"),
        ("Sheep Farming", "Animal Husbandry", "Sheep"),
        ("Pig Farming", "Animal Husbandry", "Pigs"),
        ("Rabbit Production", "Animal Husbandry", "Rabbits"),
        ("Fish Farming", "Aquaculture", None),
        ("Tilapia Production", "Aquaculture", "Tilapia"),
        ("Catfish Production", "Aquaculture", "Catfish"),
        ("Apiculture", "Apiculture", "Honey Bees"),
        ("Mixed Farming", "Mixed Farming", None),
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
    if doctype not in ("Custom Field", "Farm Type", "Crop Type"):
        return

    if doctype == "Custom Field":
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
        "Tilapia",
        "Catfish",
        "Trout",
        "Shrimp",
    ]
    for name in legacy_names:
        if frappe.db.exists("Farm Type", name):
            frappe.db.set_value(
                "Farm Type",
                name,
                {
                    "category": "Other",
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
    aquaculture_items = {"Tilapia", "Catfish", "Trout", "Shrimp"}

    def broad_type(old_value):
        if old_value in crop_items:
            return "Crop Production"
        if old_value in horticulture_items:
            return "Horticulture"
        if old_value in livestock_items:
            return "Animal Husbandry"
        if old_value in poultry_items:
            return "Poultry"
        if old_value in aquaculture_items:
            return "Aquaculture"
        return old_value

    for name, farm_type in frappe.get_all(
        "Biological Asset",
        fields=["name", "farm_type"],
        filters={"farm_type": ["in", list(crop_items | horticulture_items | livestock_items | poultry_items | aquaculture_items)]},
        as_list=True,
    ):
        frappe.db.set_value(
            "Biological Asset",
            name,
            {"farm_type": broad_type(farm_type), "managed_item": farm_type},
            update_modified=False,
        )

    for doctype, link_field in (("Farm Pen", "animal_type"), ("Farm Pond", "species"), ("Fowl Run", "bird_type")):
        for name, farm_type in frappe.get_all(
            doctype,
            fields=["name", link_field],
            filters={link_field: ["in", list(livestock_items | poultry_items | aquaculture_items)]},
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
        ("Tilapia", "Aquaculture", "Aquaculture", ["Nile Tilapia", "Red Tilapia"]),
        ("Catfish", "Aquaculture", "Aquaculture", ["African Catfish"]),
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
        if frappe.db.exists("Pest", name):
            doc = frappe.get_doc("Pest", name)
            for key, value in pest.items():
                doc.set(key, value)
            doc.save(ignore_permissions=True)
        else:
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
        if frappe.db.exists("Animal Disease", name):
            doc = frappe.get_doc("Animal Disease", name)
            for key, value in disease.items():
                doc.set(key, value)
            doc.save(ignore_permissions=True)
        else:
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
        "Farm Pond",
        "Farm Pen",
        "Fowl Run",
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
        "Outgrower Farmer",
        "Contract Farming Agreement",
        "Input Loan Disbursement",
        "Harvest Recovery",
        "Farm Activity",
        "Farm Activity Type",
    ]
    expected_reports = [
        "Farm KPI Summary",
        "Farm Budget Variance Analysis",
        "Biological Asset Register",
        "Animal Stock Ledger",
        "Contract Farming Statement",
    ]
    expected_account_names = [
        "Biological Assets",
        "Biological Asset Capital Work In Progress",
        "Biological Asset Fair Value Gain Loss",
        "Biological Asset Sales Receivable",
        "Biological Asset Sales Income",
        "Contract Farming Input Loans Receivable",
        "Contract Farming Input Clearing",
        "Contract Farming Harvest Purchases",
        "Contract Farming Grower Payable",
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
