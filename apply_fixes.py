import os
import json

base_path = r"c:\Users\havano\Documents\farm_management\farm_management"

patches = {
    "animal_stock_entry.json": {
        "rate": "item.valuation_rate"
    },
    "standard_cost_calculation_bom.json": {
        "unit": "item.stock_uom"
    }
}

for root, dirs, files in os.walk(base_path):
    for file in files:
        if file in patches:
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            patch_rules = patches[file]
            updated = False
            
            for field in data.get("fields", []):
                fname = field.get("fieldname")
                if fname in patch_rules:
                    field["fetch_from"] = patch_rules[fname]
                    updated = True
                    
            if updated:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=1)
