import os
import json

base_path = r"c:\Users\havano\Documents\farm_management\farm_management"
doctype_paths = []

for root, dirs, files in os.walk(base_path):
    if "doctype" in root:
        for file in files:
            if file.endswith(".json"):
                doctype_paths.append(os.path.join(root, file))

def analyze_architecture():
    doctypes = {}
    
    # Load all doctypes
    for path in doctype_paths:
        with open(path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                filename = os.path.basename(path).replace('.json', '')
                name = " ".join([word.capitalize() for word in filename.split('_')])
                
                # Overwrite name if exists in JSON
                if data.get("name"):
                    name = data.get("name")
                    
                doctypes[name] = {
                    "path": path,
                    "data": data,
                    "is_child": bool(data.get("istable", 0)),
                    "module": data.get("module"),
                    "fields": data.get("fields", []),
                    "links": [],
                    "child_tables": [],
                    "auto_fetches": [],
                    "missing_fetches": [],
                    "redundancies": []
                }
            except Exception as e:
                pass
                
    # Analyze
    for name, dt in doctypes.items():
        fields = dt["fields"]
        
        # Track field names to find redundancies
        field_names = [f.get("fieldname") for f in fields if f.get("fieldname")]
        
        for field in fields:
            ftype = field.get("fieldtype")
            fname = field.get("fieldname")
            options = field.get("options")
            fetch_from = field.get("fetch_from")
            
            if ftype == "Table" and options:
                dt["child_tables"].append({"field": fname, "table": options})
                
                # Check for redundancy: Does the child table repeat fields from parent?
                child_dt = doctypes.get(options)
                if child_dt:
                    child_field_names = [f.get("fieldname") for f in child_dt["fields"] if f.get("fieldname")]
                    overlap = set(field_names).intersection(set(child_field_names))
                    # Ignore common generic fields
                    overlap = overlap - {"name", "owner", "creation", "modified", "modified_by", "docstatus", "idx", "company", "cost_center"}
                    if overlap:
                        dt["redundancies"].append(f"Child table {options} repeats parent fields: {', '.join(overlap)}")
                        
            elif ftype == "Link" and options:
                dt["links"].append({"field": fname, "target": options})
                
                # Deep check for missing fetches
                if not fetch_from:
                    if options == "Item" and any(x in fname for x in ["price", "rate", "cost"]):
                        dt["missing_fetches"].append(f"Missing price fetch for Item in {fname}")
                    if options == "Item" and "uom" in fname or "unit" in fname:
                        dt["missing_fetches"].append(f"Missing UOM fetch for Item in {fname}")
                    if options == "Biological Asset" and "cost" in fname:
                        dt["missing_fetches"].append(f"Missing capitalized_cost fetch for Biological Asset in {fname}")
                    if options == "Biological Asset" and "valuation" in fname:
                        dt["missing_fetches"].append(f"Missing fair_value fetch for Biological Asset in {fname}")
                    if options == "Biological Asset Capitalization" and "cost" in fname:
                        dt["missing_fetches"].append(f"Missing cost fetch for Capitalization in {fname}")
            
            if fetch_from:
                dt["auto_fetches"].append({"field": fname, "fetch_from": fetch_from})
                
            # Non-link missing fetches
            if not fetch_from and ftype in ["Currency", "Float", "Data"]:
                if any(x in fname for x in ["price", "rate", "uom", "unit", "cost"]):
                    dt["missing_fetches"].append(f"Potential missing fetch for manual field {fname}")

    report = "# Deep Architectural Audit Report\n\n"
    for name, dt in sorted(doctypes.items(), key=lambda x: x[0]):
        if dt["missing_fetches"] or dt["redundancies"]:
            report += f"## {name}\n"
            if dt["missing_fetches"]:
                report += "- **Missing Data Flow (Auto-Fetches):**\n"
                for mf in set(dt["missing_fetches"]):
                    report += f"  - {mf}\n"
            if dt["redundancies"]:
                report += "- **Redundancies & Poor Practices:**\n"
                for r in set(dt["redundancies"]):
                    report += f"  - {r}\n"
            report += "\n"

    with open("deep_audit_report.md", "w", encoding="utf-8") as f:
        f.write(report)

if __name__ == "__main__":
    analyze_architecture()
