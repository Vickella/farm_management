import frappe
from frappe.utils import today

def run_tests():
    print("--- STARTING LIVE TESTS ---")
    errors = []

    try:
        # 1. Biological Asset
        print("Testing Biological Asset...")
        # Create Farm Type if not exists
        if not frappe.db.exists("Farm Type", "Test Crop Farm"):
            ft = frappe.get_doc({
                "doctype": "Farm Type", 
                "farm_type_name": "Test Crop Farm", 
                "category": "Crop Production",
                "managed_items": [{"managed_item_name": "Maize", "is_active": 1}]
            })
            ft.insert(ignore_permissions=True)
            
        if not frappe.db.exists("Farm Type", "Test Poultry Farm"):
            ft_poultry = frappe.get_doc({
                "doctype": "Farm Type", 
                "farm_type_name": "Test Poultry Farm", 
                "category": "Poultry",
                "managed_items": [{"managed_item_name": "Broiler", "is_active": 1}]
            })
            ft_poultry.insert(ignore_permissions=True)
            
        # Create a Farm if not exists
        if not frappe.db.exists("Farm", "Test Farm"):
            farm = frappe.get_doc({
                "doctype": "Farm", 
                "farm_name": "Test Farm", 
                "company": frappe.defaults.get_user_default("Company") or "Test Company",
                "owner_name": frappe.db.get_value("Company", {}, "name"),
                "total_land_size": 100,
                "farm_type": [{"farm_type": "Test Crop Farm"}, {"farm_type": "Test Poultry Farm"}]
            })
            farm.insert(ignore_permissions=True)
        
        farm_name = frappe.db.get_value("Farm", {}, "name")

        crop_asset = frappe.get_doc({
            "doctype": "Biological Asset",
            "asset_name": "Test Maize Crop",
            "asset_category": "Crops in Growth",
            "farm_type": "Test Crop Farm",
            "managed_item": "Maize",
            "farm": farm_name,
            "status": "Active"
        })
        crop_asset.insert(ignore_permissions=True)
        print("Biological Asset (Crop) inserted successfully!")

        livestock_asset = frappe.get_doc({
            "doctype": "Biological Asset",
            "asset_name": "Test Broilers",
            "asset_category": "Poultry",
            "farm_type": "Test Poultry Farm",
            "managed_item": "Broiler",
            "farm": farm_name,
            "status": "Active",
            "quantity": 100,
            "unit": "Bird",
            "acquisition_date": today(),
            "initial_cost": 5000,
            "net_fair_value": 5000
        })
        livestock_asset.insert(ignore_permissions=True)
        print("Biological Asset (Livestock) inserted successfully!")

        # 2. Harvest Transaction
        print("Testing Harvest Transaction...")
        # Need an item for conversion
        if not frappe.db.exists("Item", "Harvested Maize"):
            item = frappe.get_doc({"doctype": "Item", "item_code": "Harvested Maize", "item_group": "Products", "stock_uom": "Kg", "is_stock_item": 1})
            try:
                item.insert(ignore_permissions=True)
            except:
                pass
        
        harvest = frappe.get_doc({
            "doctype": "Harvest Transaction",
            "farm": farm_name,
            "biological_asset": crop_asset.name,
            "harvest_date": today(),
            "quantity_harvested": 5000,
            "unit": "kg",
            "conversion_item": "Harvested Maize",
            "target_warehouse": frappe.db.get_value("Warehouse", {}, "name")
        })
        harvest.insert(ignore_permissions=True)
        harvest.submit()
        print("Harvest Transaction submitted successfully!")

        # 3. Animal Stock Entry
        print("Testing Animal Stock Entry (Transfer)...")
        if not frappe.db.exists("Farm", "Target Farm"):
            target_farm = frappe.get_doc({
                "doctype": "Farm", 
                "farm_name": "Target Farm", 
                "company": frappe.defaults.get_user_default("Company") or "Test Company",
                "owner_name": frappe.db.get_value("Company", {}, "name"),
                "total_land_size": 100,
                "farm_type": [{"farm_type": "Test Crop Farm"}, {"farm_type": "Test Poultry Farm"}]
            })
            try:
                target_farm.insert(ignore_permissions=True)
            except:
                pass
        
        ase = frappe.get_doc({
            "doctype": "Animal Stock Entry",
            "posting_date": today(),
            "entry_type": "Transfer",
            "farm": farm_name,
            "target_farm": frappe.db.get_value("Farm", {"farm_name": "Target Farm"}, "name"),
            "biological_asset": livestock_asset.name,
            "quantity": 100,
            "unit": "Bird",
            "rate": 50
        })
        ase.insert(ignore_permissions=True)
        ase.submit()
        print("Animal Stock Entry (Transfer) submitted successfully!")
        
        # Verify Farm changed
        frappe.db.commit()
        if frappe.db.get_value("Biological Asset", livestock_asset.name, "farm") != ase.target_farm:
            errors.append("Biological Asset farm did not update after Transfer.")

        # 4. Farm BOM
        print("Testing Farm BOM...")
        if not frappe.db.exists("Project", "Test Project"):
            proj = frappe.get_doc({"doctype": "Project", "project_name": "Test Project"})
            try:
                proj.insert(ignore_permissions=True)
            except:
                pass
            
        bom = frappe.get_doc({
            "doctype": "Farm BOM",
            "bom_title": "Test BOM",
            "project_type": "Crop Production",
            "farm": farm_name,
            "project": frappe.db.get_value("Project", {}, "name"),
            "planned_quantity": 10,
            "bom_items": [
                {
                    "item": "Harvested Maize",
                    "item_description": "Harvested Maize",
                    "quantity": 5,
                    "unit": "kg",
                    "rate": 10
                }
            ]
        })
        bom.insert(ignore_permissions=True)
        print("Farm BOM created successfully!")

        # 5. Contract Farming Agreement
        print("Testing Contract Farming...")
        if not frappe.db.exists("Outgrower Farmer", "Test Farmer"):
            farmer = frappe.get_doc({"doctype": "Outgrower Farmer", "farmer_name": "Test Farmer", "national_id": "ID-12345"})
            try:
                farmer.insert(ignore_permissions=True)
            except:
                pass
                
        cfa = frappe.get_doc({
            "doctype": "Contract Farming Agreement",
            "farmer": frappe.db.get_value("Outgrower Farmer", {}, "name"),
            "farm": farm_name,
            "contract_type": "Giving Contract (Asset)",
            "contract_start_date": today(),
            "contract_end_date": frappe.utils.add_days(today(), 30),
            "crop_type": frappe.db.get_value("Crop Type", {}, "name") or "Test Crop",
            "contracted_area_ha": 5,
            "production_target": 1000,
            "unit": "kg",
            "agreed_purchase_price_per_unit": 2,
            "inputs_provided": [
                {
                    "input_type": "Seed",
                    "item": "Harvested Maize",
                    "quantity": 10,
                    "value": 100
                }
            ]
        })
        cfa.insert(ignore_permissions=True)
        print("Contract Farming Agreement created successfully!")

    except Exception as e:
        import traceback
        errors.append(traceback.format_exc())

    print("\n--- TEST RESULTS ---")
    if errors:
        print(f"FAILED with {len(errors)} errors:")
        for err in errors:
            print(err)
    else:
        print("ALL TESTS PASSED!")
