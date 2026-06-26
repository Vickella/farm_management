import os
import json

base_path = r"c:\Users\havano\Documents\farm_management\farm_management"

# 1. Remove is_active from Farm Type Managed Item
managed_item_path = os.path.join(base_path, "farm_setup", "doctype", "farm_type_managed_item", "farm_type_managed_item.json")
if os.path.exists(managed_item_path):
    with open(managed_item_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Remove is_active
    data["fields"] = [f for f in data["fields"] if f.get("fieldname") != "is_active"]
    
    with open(managed_item_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1)

# 2. Make total_cost read-only in Farm BOM Item
bom_item_path = os.path.join(base_path, "farm_bom", "doctype", "farm_bom_item", "farm_bom_item.json")
if os.path.exists(bom_item_path):
    with open(bom_item_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for field in data["fields"]:
        if field.get("fieldname") == "total_cost":
            field["read_only"] = 1
            
    with open(bom_item_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1)

# 3. Make total_estimated_cost read-only in Farm BOM
bom_path = os.path.join(base_path, "farm_bom", "doctype", "farm_bom", "farm_bom.json")
if os.path.exists(bom_path):
    with open(bom_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for field in data["fields"]:
        if field.get("fieldname") == "total_estimated_cost":
            field["read_only"] = 1
            
    with open(bom_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1)

# 4. Make cost read-only in Biological Asset Capitalization
cap_path = os.path.join(base_path, "biological_asset", "doctype", "biological_asset_capitalization", "biological_asset_capitalization.json")
if os.path.exists(cap_path):
    with open(cap_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for field in data["fields"]:
        if field.get("fieldname") == "cost":
            field["read_only"] = 1
            
    with open(cap_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1)

print("JSON modifications complete.")
