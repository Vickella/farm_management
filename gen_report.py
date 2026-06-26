import json

with open("audit_report.json", "r", encoding='utf-8') as f:
    data = json.load(f)

md = "# Farm Management Architecture Audit Report\n\n"
md += "This report analyzes parent-child relationships and auto-fetching fields (e.g. UOM, Unit Price) across all doctypes.\n\n"

for dt in data:
    if dt.get("name"):
        name = dt["name"]
        md += f"## {name}\n"
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
