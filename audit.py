import os
import json

base_path = r"c:\Users\havano\Documents\farm_management\farm_management"
doctype_paths = []

for root, dirs, files in os.walk(base_path):
    if "doctype" in root:
        for file in files:
            if file.endswith(".json"):
                doctype_paths.append(os.path.join(root, file))

report = []
for path in doctype_paths:
    with open(path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            
            # Extract name from filename
            filename = os.path.basename(path).replace('.json', '')
            # Format it Title Case for display
            name = " ".join([word.capitalize() for word in filename.split('_')])
            
            istable = data.get("istable", 0)
            fields = data.get("fields", [])
            
            child_tables = []
            links = []
            auto_fetches = []
            missing_fetches = []
            
            for field in fields:
                ftype = field.get("fieldtype")
                fname = field.get("fieldname")
                options = field.get("options")
                fetch_from = field.get("fetch_from")
                
                if ftype == "Table":
                    child_tables.append({"field": fname, "table": options})
                elif ftype == "Link" and options:
                    links.append({"field": fname, "target": options})
                
                if fetch_from:
                    auto_fetches.append({"field": fname, "fetch_from": fetch_from})
                elif ftype in ["Currency", "Float", "Data"] and any(x in fname for x in ["price", "rate", "uom", "unit", "cost"]):
                    # Potential missing fetch
                    missing_fetches.append(fname)
                    
            report.append({
                "name": name,
                "is_child": bool(istable),
                "child_tables": child_tables,
                "links": links,
                "auto_fetches": auto_fetches,
                "potential_missing_fetches": missing_fetches
            })
        except Exception as e:
            pass

md = "# Farm Management Architecture Audit Report\n\n"
md += "This report analyzes parent-child relationships and auto-fetching fields (e.g. UOM, Unit Price) across all doctypes.\n\n"

for dt in sorted(report, key=lambda x: x["name"]):
    md += f"## {dt['name']}\n"
    md += f"- **Type:** {'Child Table' if dt['is_child'] else 'Parent DocType'}\n"
    
    if dt["child_tables"]:
        md += "- **Child Tables:**\n"
        for ct in dt["child_tables"]:
            md += f"  - `{ct['field']}` (Linked to `{ct['table']}`)\n"
    
    if dt["links"]:
        md += "- **Linked DocTypes:**\n"
        for link in dt["links"]:
            md += f"  - `{link['field']}` -> `{link['target']}`\n"
    
    if dt["auto_fetches"]:
        md += "- **Auto-Fetching Fields:**\n"
        for fetch in dt["auto_fetches"]:
            md += f"  - `{fetch['field']}` is populated from `{fetch['fetch_from']}`\n"
    
    if dt["potential_missing_fetches"]:
        md += "- **Potential Missing Auto-Fetches (Needs Review):**\n"
        md += f"  - {', '.join(dt['potential_missing_fetches'])}\n"
    
    md += "\n"

with open("C:/Users/havano/.gemini/antigravity-ide/brain/25813e12-703d-4eec-8381-add5fb012a83/architecture_audit.md", "w", encoding='utf-8') as f:
    f.write(md)
