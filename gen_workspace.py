import json

workspace = {
    "creation": "2024-01-01 00:00:00.000000",
    "docstatus": 0,
    "doctype": "Workspace",
    "for_user": "",
    "hide_custom": 0,
    "icon": "agriculture",
    "indicator_color": "green",
    "is_hidden": 0,
    "is_standard": 1,
    "public": 1,
    "roles": [{"role": "System Manager"}, {"role": "Administrator"}],
    "label": "Farm Management",
    "module": "Farm Setup",
    "name": "Farm Management",
    "title": "Farm Management",
    "modified": "2024-01-01 00:00:00.000000",
    "modified_by": "Administrator",
    "owner": "Administrator",
    "sequence_id": 1.0,
    "type": "Workspace",
}

groups = {
    "FARM SETUP": [
        "Farm", 
        "Farm Type", 
        "Agriculture Project Type", 
        "Crop Type", 
        "Farm Management Settings"
    ],
    "CROP PRODUCTION": [
        "Crop Cycle", 
        "Field Management", 
        "Harvest Log"
    ],
    "POULTRY MANAGEMENT": [
        "Poultry Flock", 
        "Broiler Batch", 
        "Egg Production Log", 
        "Poultry Infrastructure"
    ],
    "FISH FARMING": [
        "Fish Batch", 
        "Pond Management", 
        "Water Quality Log", 
        "Fish Feeding Log"
    ],
    "LIVESTOCK MANAGEMENT": [
        "Livestock Individual", 
        "Animal Stock Entry", 
        "Livestock Species", 
        "Livestock Breed", 
        "Livestock Health Event", 
        "Livestock Breeding Record",
        "Animal Herd",
        "Cattle Herd",
        "Cattle Infrastructure",
        "Breeding Log",
        "Meat Production Log",
        "Goat Herd",
        "Goat Breeding Log",
        "Goat Meat Milk Log",
        "Pig Batch",
        "Farrowing Log",
        "Pig Infrastructure"
    ],
    "DAIRY MANAGEMENT": [
        "Dairy Cow Herd", 
        "Dairy Infrastructure", 
        "Lactation Cycle", 
        "Milk Yield Log",
        "Dairy Milking Cycle"
    ],
    "BIOLOGICAL ASSETS IAS 41": [
        "Biological Asset", 
        "Biological Asset Capitalization", 
        "Biological Asset Valuation", 
        "Harvest Transaction"
    ],
    "FINANCIAL MANAGEMENT": [
        "Farm Cashbook", 
        "Farm Budget", 
        "Farm Budget Item",
        "Budget Forecasting",
        "Budget Forecasting Expense"
    ],
    "INVENTORY MANAGEMENT": [
        "Farm BOM",
        "Farm BOM Item",
        "Standard Cost Calculation BOM"
    ],
    "REPORTING & ANALYTICS": [
        "Farm KPI Summary",
        "Farm Budget Variance Analysis",
        "Biological Asset Register",
        "Animal Stock Ledger",
        "Contract Farming Statement"
    ],
    "FARM INFRASTRUCTURE": [
        "Farm Field",
        "Farm Pen",
        "Farm Pond",
        "Fowl Run"
    ],
    "DISEASE AND PEST INTELLIGENCE": [
        "Disease Incident",
        "Animal Disease",
        "Pest"
    ],
    "CONTRACT FARMING": [
        "Contract Farming Agreement",
        "Outgrower Farmer",
        "Input Loan Disbursement",
        "Harvest Recovery"
    ],
    "FARM CALENDAR": [
        "Farm Activity",
        "Farm Activity Type"
    ]
}

shortcuts = [
    "Farm", 
    "Biological Asset", 
    "Farm Cashbook", 
    "Farm Budget", 
    "Livestock Individual"
]

content = [
    {"id": "farm-management-header", "type": "header", "data": {"text": "Farm Management", "col": 12}}
]

for name in groups.keys():
    content.append({
        "id": f"card-{name.lower().replace(' & ', '-').replace(' ', '-')}",
        "type": "card",
        "data": {"card_name": name, "col": 4}
    })

content.append({"id": "spacer-1", "type": "spacer", "data": {"col": 12}})
content.append({"id": "shortcuts-header", "type": "header", "data": {"text": "Shortcuts", "col": 12}})

for shortcut in shortcuts:
    content.append({
        "id": f"shortcut-{shortcut.lower().replace(' ', '-')}",
        "type": "shortcut",
        "data": {"shortcut_name": shortcut, "col": 3}
    })

workspace["content"] = json.dumps(content)

links = []
for group_name, doc_types in groups.items():
    links.append({
        "type": "Card Break",
        "label": group_name,
        "hidden": 0,
        "is_query_report": 0,
        "onboard": 0,
        "link_count": len(doc_types)
    })
    for dt in doc_types:
        is_report = "Report" in dt or "Summary" in dt or "Analysis" in dt or "Ledger" in dt or "Statement" in dt
        link_type = "Report" if is_report else "DocType"
        links.append({
            "type": "Link",
            "label": dt,
            "link_type": link_type,
            "link_to": dt,
            "hidden": 0,
            "is_query_report": 1 if is_report else 0,
            "onboard": 0
        })

workspace["links"] = links

ws_shortcuts = []
for shortcut in shortcuts:
    ws_shortcuts.append({
        "label": shortcut,
        "type": "DocType",
        "link_to": shortcut,
        "doc_view": "List",
        "color": "Grey"
    })
    
workspace["shortcuts"] = ws_shortcuts

with open("c:/Users/havano/Documents/farm_management/farm_management/farm_setup/workspace/farm_management/farm_management.json", "w") as f:
    json.dump(workspace, f, indent=1)
