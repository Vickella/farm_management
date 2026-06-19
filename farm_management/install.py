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

LEGACY_PROJECT_CUSTOM_FIELDS = [
    "Project-breed",
    "Project-initial_quantity",
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
    (
        "Livestock Tracking",
        [
            ("Livestock Individual", "DocType"),
            ("Livestock Health Event", "DocType"),
            ("Livestock Breeding Record", "DocType"),
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
    ("Weather", [("Farm Weather Forecast", "Page", "farm-weather")]),
    ("Reports", [("Farm KPI Summary", "Report"), ("Farm Budget Variance Analysis", "Report")]),
]

WORKSPACE_SHORTCUTS = [
    "Farm",
    "Biological Asset",
    "Livestock Individual",
    "Livestock Health Event",
    "Disease Incident",
    "Farm BOM",
    "Farm Budget",
    "Contract Farming Agreement",
    ("Farm Weather", "URL", "farm-weather"),
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
    remove_legacy_project_custom_fields()
    seed_fixture_data()
    seed_livestock_breeds()
    seed_pests()
    seed_animal_diseases()
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


def seed_fixture_data():
    fixtures_dir = Path(frappe.get_app_path("farm_management")).parent / "fixtures"
    if not fixtures_dir.exists():
        return

    fixture_paths = sorted(fixtures_dir.glob("*.json"), key=get_fixture_sort_key)
    for fixture_path in fixture_paths:
        with fixture_path.open(encoding="utf-8") as fixture_file:
            records = json.load(fixture_file)

        for record in records:
            existing_name = get_fixture_existing_name(record)
            if existing_name:
                update_existing_fixture_record(record, existing_name)
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
    if doctype != "Custom Field":
        return

    doc = frappe.get_doc(doctype, existing_name)
    for key, value in record.items():
        if key != "doctype":
            doc.set(key, value)
    doc.save(ignore_permissions=True)


def seed_livestock_breeds():
    breeds = {
        "Cattle": ["Brahman", "Hereford", "Angus", "Simmental", "Mashona", "Tuli", "Nguni", "Charolais", "Limousin"],
        "Goat": ["Boer", "Kalahari Red", "Savanna", "Indigenous Mashona Goat", "Toggenburg", "Saanen"],
        "Sheep": ["Merino", "Dorper", "Suffolk", "Damara", "Meatmaster"],
        "Pig": ["Large White", "Landrace", "Duroc", "Pietrain", "Indigenous (Mukota)"],
    }
    for species, breed_names in breeds.items():
        for breed in breed_names:
            description = f"{species} breed used in livestock production."
            values = {"category": "Animal Husbandry", "description": description}
            if frappe.db.exists("Farm Type", breed):
                frappe.db.set_value("Farm Type", breed, values)
            else:
                frappe.get_doc(
                    {
                        "doctype": "Farm Type",
                        "farm_type_name": breed,
                        **values,
                    }
                ).insert(ignore_permissions=True)


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
        if isinstance(shortcut, tuple):
            label, shortcut_type, link_to = shortcut
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
