# Farm Management App Documentation

Farm Management is a Frappe/ERPNext v15 custom app for managing agricultural operations across farm setup, infrastructure, biological assets, disease intelligence, farm calendars, BOMs, budgeting, and contract farming.

## Workspace

The app provides a public Workspace named **Farm Management** under the **Farm Setup** module.

Workspace cards:

- Farm Setup: Farm, Farm Type, Crop Type, Farm Management Settings
- Farm Infrastructure: Farm Field, Farm Pond, Farm Pen, Fowl Run
- Biological Assets: Biological Asset, Harvest Transaction
- Disease and Pest Intelligence: Disease Incident, Pest, Animal Disease
- Farm BOM and Budgeting: Farm BOM, Farm Budget
- Contract Farming: Outgrower Farmer, Contract Farming Agreement, Input Loan Disbursement, Harvest Recovery
- Farm Calendar: Farm Activity, Farm Activity Type
- Reports: Farm KPI Summary, Farm Budget Variance Analysis

Workspace shortcuts:

- Farm
- Biological Asset
- Disease Incident
- Farm BOM
- Farm Budget
- Contract Farming Agreement

## DocType Index

| Module | DocTypes |
| --- | --- |
| Farm Setup | Farm, Farm Type, Crop Type, Farm Management Settings, Farm Type Multiselect |
| Farm Infrastructure | Farm Field, Farm Pond, Farm Pen, Fowl Run |
| Biological Assets | Biological Asset, Harvest Transaction |
| Disease Intelligence | Disease Incident, Pest, Animal Disease |
| Farm BOM | Farm BOM, Farm BOM Item |
| Project Costing | Farm Budget, Farm Budget Item |
| Contract Farming | Outgrower Farmer, Contract Farming Agreement, Input Loan Disbursement, Harvest Recovery |
| Farm Calendar | Farm Activity, Farm Activity Type |

## Farm Setup

### Farm

Primary master record for a farm or agricultural site.

Links:

| Field | Target |
| --- | --- |
| owner_name | Customer |
| farm_manager | Employee |
| farm_type | Farm Type Multiselect |

Fields:

| Field | Label | Type | Required | Options or Target |
| --- | --- | --- | --- | --- |
| farm_name | Farm Name | Data | Yes |  |
| owner_name | Owner | Link | Yes | Customer |
| farm_registration_number | Farm Registration Number | Data | No |  |
| operational_status | Operational Status | Select | Yes | Active, Dormant, Decommissioned |
| farm_manager | Farm Manager | Link | No | Employee |
| location | Location | Data | No |  |
| gps_coordinates | GPS Coordinates | Geolocation | No |  |
| total_land_size | Total Land Size (Ha) | Float | Yes |  |
| irrigation_type | Irrigation Type | Select | No | None, Drip, Sprinkler, Flood, Centre Pivot, Rainfed |
| water_source | Water Source | Select | No | Borehole, River, Dam, Municipal, Rainwater Harvesting |
| soil_type | Soil Type | Select | No | Sandy, Clay, Loam, Sandy Loam, Clay Loam, Silt |
| climate_zone | Climate Zone | Select | No | Region 1, Region 2, Region 3, Region 4, Region 5 |
| farm_type | Farm Types | Table MultiSelect | Yes | Farm Type Multiselect |

### Farm Type

Master record for farming categories, species, crop families, or production types.

Links: none.

Fields:

| Field | Label | Type | Required | Options or Target |
| --- | --- | --- | --- | --- |
| farm_type_name | Farm Type Name | Data | Yes |  |
| category | Category | Select | Yes | Crop Farming, Horticulture, Animal Husbandry, Poultry, Aquaculture |
| description | Description | Small Text | No |  |

### Crop Type

Master record for crop varieties and expected growth/yield information.

Links:

| Field | Target |
| --- | --- |
| category | Farm Type |

Fields:

| Field | Label | Type | Required | Options or Target |
| --- | --- | --- | --- | --- |
| crop_name | Crop Name | Data | Yes |  |
| category | Category | Link | No | Farm Type |
| growth_period_days | Growth Period (Days) | Int | No |  |
| expected_yield_per_ha | Expected Yield per Ha | Float | No |  |
| yield_unit | Yield Unit | Select | No | kg, Tonne, Bag, Crate |
| notes | Notes | Small Text | No |  |

### Farm Management Settings

Single settings document for accounts, AI configuration, and scheduler feature flags.

Links:

| Field | Target |
| --- | --- |
| biological_asset_account | Account |
| fair_value_gain_loss_account | Account |
| default_cost_center | Cost Center |

Fields:

| Field | Label | Type | Required | Options or Target |
| --- | --- | --- | --- | --- |
| biological_asset_account | Biological Asset Account | Link | No | Account |
| fair_value_gain_loss_account | Fair Value/Gain Loss Account | Link | No | Account |
| default_cost_center | Default Cost Center | Link | No | Cost Center |
| ai_api_key | AI API Key | Password | No |  |
| ai_provider | AI Provider | Select | No | OpenAI, Anthropic, Local |
| enable_ai_assistant | Enable AI Assistant | Check | No |  |
| enable_auto_activity_generation | Enable Auto Activity Generation | Check | No |  |
| enable_fair_value_scheduler | Enable Fair Value Scheduler | Check | No |  |

### Farm Type Multiselect

Child table used by Farm to select multiple farm types.

Links:

| Field | Target |
| --- | --- |
| farm_type | Farm Type |

Fields:

| Field | Label | Type | Required | Options or Target |
| --- | --- | --- | --- | --- |
| farm_type | Farm Type | Link | Yes | Farm Type |

## Farm Infrastructure

### Farm Field

Represents a field or crop production block on a farm.

Links:

| Field | Target |
| --- | --- |
| farm | Farm |
| crop_assigned | Crop Type |

Fields:

| Field | Label | Type | Required | Options or Target |
| --- | --- | --- | --- | --- |
| naming_series | Series | Select | No | FF-.#### |
| field_number | Field Number | Data | Yes |  |
| farm | Farm | Link | Yes | Farm |
| current_status | Status | Select | Yes | Active, Fallow, Under Preparation, Harvested |
| field_size_ha | Field Size (Ha) | Float | Yes |  |
| crop_assigned | Crop Assigned | Link | No | Crop Type |
| soil_type | Soil Type | Select | No | Sandy, Clay, Loam, Sandy Loam, Clay Loam, Silt |
| irrigation_method | Irrigation Method | Select | No | None, Drip, Sprinkler, Flood |
| last_harvest_date | Last Harvest Date | Date | No |  |
| notes | Notes | Small Text | No |  |

### Farm Pond

Aquaculture infrastructure record for ponds and water quality.

Links:

| Field | Target |
| --- | --- |
| farm | Farm |
| species | Farm Type |

Fields:

| Field | Label | Type | Required | Options or Target |
| --- | --- | --- | --- | --- |
| naming_series | Series | Select | No | FP-.#### |
| pond_number | Pond Number | Data | Yes |  |
| farm | Farm | Link | Yes | Farm |
| current_status | Status | Select | Yes | Active, Dry, Under Maintenance |
| species | Species | Link | No | Farm Type |
| depth_meters | Depth (m) | Float | No |  |
| water_capacity_litres | Water Capacity (L) | Float | No |  |
| stocking_date | Stocking Date | Date | No |  |
| harvest_projection_date | Projected Harvest Date | Date | No |  |
| water_quality_ph | pH | Float | No |  |
| water_quality_temperature | Temperature (C) | Float | No |  |
| water_quality_oxygen_ppm | Oxygen (ppm) | Float | No |  |

### Farm Pen

Livestock pen, kraal, stall, or shed record.

Links:

| Field | Target |
| --- | --- |
| farm | Farm |
| animal_type | Farm Type |

Fields:

| Field | Label | Type | Required | Options or Target |
| --- | --- | --- | --- | --- |
| naming_series | Series | Select | No | FPN-.#### |
| pen_number | Pen Number | Data | Yes |  |
| farm | Farm | Link | Yes | Farm |
| pen_type | Pen Type | Select | No | Kraal, Pen, Stall, Shed |
| animal_type | Animal Type | Link | No | Farm Type |
| current_status | Status | Select | No | Active, Empty, Under Maintenance |
| capacity | Capacity | Int | No |  |
| current_occupancy | Current Occupancy | Int | No |  |
| occupancy_rate | Occupancy Rate (%) | Float | No |  |
| vaccination_status | Vaccination Status | Select | No | Up to Date, Due, Overdue |
| notes | Notes | Small Text | No |  |

### Fowl Run

Poultry housing record for bird runs and flock capacity.

Links:

| Field | Target |
| --- | --- |
| farm | Farm |
| bird_type | Farm Type |

Fields:

| Field | Label | Type | Required | Options or Target |
| --- | --- | --- | --- | --- |
| naming_series | Series | Select | No | FR-.#### |
| run_number | Run Number | Data | Yes |  |
| farm | Farm | Link | Yes | Farm |
| bird_type | Bird Type | Link | No | Farm Type |
| current_status | Status | Select | No | Active, Empty, Cleaning |
| capacity | Capacity | Int | No |  |
| current_flock_size | Current Flock Size | Int | No |  |
| mortality_rate_percent | Mortality Rate (%) | Float | No |  |
| temperature_celsius | Temperature (C) | Float | No |  |
| feeding_schedule | Feeding Schedule | Select | No | Ad Lib, Restricted, Timed |

## Biological Assets

### Biological Asset

Tracks livestock, poultry, crops in growth, and aquaculture assets with IFRS 41 fair value data.

Links:

| Field | Target |
| --- | --- |
| farm | Farm |
| farm_type | Farm Type |
| linked_project | Project |

Fields:

| Field | Label | Type | Required | Options or Target |
| --- | --- | --- | --- | --- |
| naming_series | Series | Select | No | BA-.#### |
| asset_name | Asset Name | Data | Yes |  |
| farm | Farm | Link | Yes | Farm |
| asset_category | Asset Category | Select | Yes | Livestock, Poultry, Crops in Growth, Aquaculture |
| farm_type | Species/Crop | Link | Yes | Farm Type |
| status | Status | Select | Yes | Active, Harvested, Sold, Dead Loss |
| growth_stage | Growth Stage | Select | Yes | Immature, Mature, Producing, Ready for Harvest |
| linked_project | Linked Project | Link | No | Project |
| acquisition_date | Acquisition Date | Date | Yes |  |
| quantity | Quantity | Float | Yes |  |
| unit | Unit | Select | Yes | Head, Bird, Kg, Hectare, Fingerling |
| average_weight_kg | Average Weight Kg | Float | No |  |
| mortality_to_date | Mortality To Date | Float | No |  |
| initial_cost | Initial Cost | Currency | Yes |  |
| current_fair_value | Current Fair Value | Currency | No |  |
| cost_to_sell | Estimated Cost to Sell | Currency | No |  |
| net_fair_value | Net Fair Value | Currency | No |  |
| accumulated_gain_loss | Accumulated Fair Value Gain/Loss | Currency | No |  |
| last_valuation_date | Last Valuation Date | Date | No |  |
| notes | Notes | Small Text | No |  |

### Harvest Transaction

Submittable harvest record for biological assets, optionally creating a Stock Entry.

Links:

| Field | Target |
| --- | --- |
| farm | Farm |
| biological_asset | Biological Asset |
| conversion_item | Item |
| stock_entry | Stock Entry |

Fields:

| Field | Label | Type | Required | Options or Target |
| --- | --- | --- | --- | --- |
| naming_series | Series | Select | No | HT-.#### |
| farm | Farm | Link | Yes | Farm |
| biological_asset | Biological Asset | Link | Yes | Biological Asset |
| harvest_date | Harvest Date | Date | Yes |  |
| quantity_harvested | Quantity Harvested | Float | Yes |  |
| unit | Unit | Select | Yes | kg, Tonne, Bag, Head, Bird |
| quality_grade | Quality Grade | Select | No | Grade A, Grade B, Grade C, Off-grade |
| conversion_item | Conversion Item | Link | No | Item |
| harvest_value | Harvest Value | Currency | No |  |
| stock_entry | Stock Entry | Link | No | Stock Entry |
| notes | Notes | Small Text | No |  |

## Disease Intelligence

### Pest

Master record for crop and farm pests, symptoms, and treatment guidance.

Links: none.

Fields:

| Field | Label | Type | Required | Options or Target |
| --- | --- | --- | --- | --- |
| pest_name | Pest Name | Data | Yes |  |
| scientific_name | Scientific Name | Data | No |  |
| pest_type | Pest Type | Select | Yes | Insect, Fungal, Bacterial, Viral, Weed, Rodent |
| affects | Affects | Select | No | Crops, Livestock, Poultry, Aquaculture, All |
| severity_level | Severity Level | Select | Yes | Low, Medium, High, Critical |
| signs_and_symptoms | Signs and Symptoms | Text Editor | No |  |
| causes | Causes | Small Text | No |  |
| recommended_treatment | Recommended Treatment | Text Editor | No |  |
| chemical_treatment | Chemical Treatment | Small Text | No |  |
| organic_treatment | Organic Treatment | Small Text | No |  |

### Animal Disease

Master record for animal diseases, symptoms, prevention, and treatment.

Links: none.

Fields:

| Field | Label | Type | Required | Options or Target |
| --- | --- | --- | --- | --- |
| disease_name | Disease Name | Data | Yes |  |
| affects | Affects | Select | No | Cattle, Goats, Sheep, Pigs, Poultry, Aquaculture, All Livestock |
| mortality_risk | Mortality Risk | Select | Yes | Low, Medium, High, Very High |
| is_notifiable | Is Notifiable | Check | No |  |
| zoonotic_risk | Zoonotic Risk | Check | No |  |
| vaccination_available | Vaccination Available | Check | No |  |
| symptoms | Symptoms | Text Editor | Yes |  |
| prevention_method | Prevention Method | Text Editor | No |  |
| vaccination_schedule | Vaccination Schedule | Small Text | No |  |
| treatment | Treatment | Text Editor | No |  |

### Disease Incident

Incident record for pest outbreaks or animal disease events on a farm.

Links:

| Field | Target |
| --- | --- |
| farm | Farm |
| pest | Pest |
| animal_disease | Animal Disease |
| reported_by | Employee |

Fields:

| Field | Label | Type | Required | Options or Target |
| --- | --- | --- | --- | --- |
| naming_series | Series | Select | No | DI-.#### |
| farm | Farm | Link | Yes | Farm |
| incident_date | Incident Date | Date | Yes |  |
| incident_type | Incident Type | Select | Yes | Pest, Animal Disease |
| pest | Pest | Link | No | Pest |
| animal_disease | Animal Disease | Link | No | Animal Disease |
| severity | Severity | Select | Yes | Low, Medium, High, Critical |
| affected_area_or_animals | Affected Area or Animals | Small Text | Yes |  |
| treatment_applied | Treatment Applied | Text Editor | No |  |
| treatment_cost | Treatment Cost | Currency | No |  |
| loss_estimate | Loss Estimate | Currency | No |  |
| resolved | Resolved | Check | No |  |
| resolution_date | Resolution Date | Date | No |  |
| reported_by | Reported By | Link | No | Employee |
| notes | Notes | Small Text | No |  |

## Farm BOM

### Farm BOM

Production template for expected inputs, quantities, costs, and cycle duration.

Links:

| Field | Target |
| --- | --- |
| farm | Farm |
| bom_items | Farm BOM Item |

Fields:

| Field | Label | Type | Required | Options or Target |
| --- | --- | --- | --- | --- |
| naming_series | Series | Select | No | FBOM-.#### |
| bom_title | BOM Title | Data | Yes |  |
| project_type | Project Type | Select | Yes | Crop Production, Poultry Production, Fish Farming, Dairy Production, Goat Farming, Pig Farming, Greenhouse Farming |
| farm | Farm | Link | No | Farm |
| planned_quantity | Planned Quantity | Float | Yes |  |
| planned_quantity_unit | Planned Quantity Unit | Select | No | Birds, Head, Hectare, Kg, Units |
| production_cycle_days | Production Cycle Days | Int | No |  |
| planned_start_date | Planned Start Date | Date | No |  |
| planned_end_date | Planned End Date | Date | No |  |
| total_estimated_cost | Total Estimated Cost | Currency | No |  |
| bom_items | BOM Items | Table | Yes | Farm BOM Item |
| notes | Notes | Small Text | No |  |

### Farm BOM Item

Child table for Farm BOM input lines.

Links:

| Field | Target |
| --- | --- |
| item | Item |

Fields:

| Field | Label | Type | Required | Options or Target |
| --- | --- | --- | --- | --- |
| item_category | Item Category | Select | Yes | Feed, Medication, Seed, Fertilizer, Chemical, Labor, Utility, Equipment, Other |
| item_description | Item Description | Data | Yes |  |
| item | Item | Link | No | Item |
| quantity | Quantity | Float | Yes |  |
| unit | Unit | Select | Yes | kg, Litre, Bag, Piece, Hour, Day |
| unit_cost | Unit Cost | Currency | No |  |
| total_cost | Total Cost | Currency | No |  |

## Project Costing

### Farm Budget

Budget document for planned and actual farm or project costs.

Links:

| Field | Target |
| --- | --- |
| farm | Farm |
| project | Project |
| farm_bom | Farm BOM |
| budget_items | Farm Budget Item |

Fields:

| Field | Label | Type | Required | Options or Target |
| --- | --- | --- | --- | --- |
| naming_series | Series | Select | No | FBUDG-.#### |
| budget_title | Budget Title | Data | Yes |  |
| farm | Farm | Link | Yes | Farm |
| project | Project | Link | No | Project |
| farm_bom | Farm BOM | Link | No | Farm BOM |
| budget_period_start | Budget Period Start | Date | Yes |  |
| budget_period_end | Budget Period End | Date | Yes |  |
| status | Status | Select | Yes | Draft, Approved, Active, Closed |
| budget_items | Budget Items | Table | No | Farm Budget Item |
| total_budget | Total Budget | Currency | No |  |
| total_actual | Total Actual | Currency | No |  |
| total_variance | Total Variance | Currency | No |  |

### Farm Budget Item

Child table for Farm Budget budget lines and variance tracking.

Links: none.

Fields:

| Field | Label | Type | Required | Options or Target |
| --- | --- | --- | --- | --- |
| item_category | Item Category | Select | No | Feed, Medication, Seed, Fertilizer, Chemical, Labor, Utility, Equipment, Other |
| item_description | Item Description | Data | Yes |  |
| budgeted_quantity | Budgeted Quantity | Float | No |  |
| budgeted_unit_cost | Budgeted Unit Cost | Currency | No |  |
| budgeted_amount | Budgeted Amount | Currency | No |  |
| actual_amount | Actual Amount | Currency | No |  |
| variance | Variance | Currency | No |  |
| variance_percent | Variance Percent | Float | No |  |
| variance_type | Variance Type | Select | No | Favourable, Adverse |

## Contract Farming

### Outgrower Farmer

Master record for external farmers participating in contract farming.

Links:

| Field | Target |
| --- | --- |
| primary_crop | Crop Type |

Fields:

| Field | Label | Type | Required | Options or Target |
| --- | --- | --- | --- | --- |
| naming_series | Series | Select | No | OGF-.#### |
| farmer_name | Farmer Name | Data | Yes |  |
| national_id | National ID | Data | Yes |  |
| phone | Phone | Data | No |  |
| email | Email | Data | No |  |
| location | Location | Data | No |  |
| farm_size_ha | Farm Size Ha | Float | No |  |
| primary_crop | Primary Crop | Link | No | Crop Type |
| is_active | Is Active | Check | No |  |
| bank_name | Bank Name | Data | No |  |
| bank_account_number | Bank Account Number | Data | No |  |

### Contract Farming Agreement

Submittable contract record between a farm and an outgrower farmer.

Links:

| Field | Target |
| --- | --- |
| farmer | Outgrower Farmer |
| farm | Farm |
| crop_type | Crop Type |

Fields:

| Field | Label | Type | Required | Options or Target |
| --- | --- | --- | --- | --- |
| naming_series | Series | Select | No | CFA-.#### |
| farmer | Farmer | Link | Yes | Outgrower Farmer |
| farm | Farm | Link | Yes | Farm |
| status | Status | Select | Yes | Draft, Active, Completed, Defaulted, Cancelled |
| contract_start_date | Contract Start Date | Date | Yes |  |
| contract_end_date | Contract End Date | Date | Yes |  |
| crop_type | Crop Type | Link | Yes | Crop Type |
| contracted_area_ha | Contracted Area Ha | Float | Yes |  |
| production_target_kg | Production Target Kg | Float | Yes |  |
| agreed_purchase_price_per_kg | Agreed Purchase Price Per Kg | Currency | Yes |  |
| total_expected_purchase | Total Expected Purchase | Currency | No |  |
| seed_provided | Seed Provided | Check | No |  |
| seed_value | Seed Value | Currency | No |  |
| fertilizer_provided | Fertilizer Provided | Check | No |  |
| fertilizer_value | Fertilizer Value | Currency | No |  |
| chemical_provided | Chemical Provided | Check | No |  |
| chemical_value | Chemical Value | Currency | No |  |
| total_input_loan | Total Input Loan | Currency | No |  |
| quality_standards | Quality Standards | Text Editor | No |  |

### Input Loan Disbursement

Record of input loans issued to an outgrower under a contract.

Links:

| Field | Target |
| --- | --- |
| agreement | Contract Farming Agreement |
| farmer | Outgrower Farmer |
| item | Item |

Fields:

| Field | Label | Type | Required | Options or Target |
| --- | --- | --- | --- | --- |
| naming_series | Series | Select | No | ILD-.#### |
| agreement | Agreement | Link | Yes | Contract Farming Agreement |
| farmer | Farmer | Link | Yes | Outgrower Farmer |
| disbursement_date | Disbursement Date | Date | Yes |  |
| input_type | Input Type | Select | Yes | Seed, Fertilizer, Chemical, Cash |
| item | Item | Link | No | Item |
| quantity | Quantity | Float | No |  |
| unit | Unit | Data | No |  |
| value | Value | Currency | Yes |  |
| recovered | Recovered | Check | No |  |
| recovery_date | Recovery Date | Date | No |  |
| recovery_reference | Recovery Reference | Data | No |  |
| notes | Notes | Small Text | No |  |

### Harvest Recovery

Record of produce recovered from an outgrower and related loan deductions.

Links:

| Field | Target |
| --- | --- |
| agreement | Contract Farming Agreement |
| farmer | Outgrower Farmer |

Fields:

| Field | Label | Type | Required | Options or Target |
| --- | --- | --- | --- | --- |
| naming_series | Series | Select | No | HR-.#### |
| agreement | Agreement | Link | Yes | Contract Farming Agreement |
| farmer | Farmer | Link | Yes | Outgrower Farmer |
| recovery_date | Recovery Date | Date | Yes |  |
| quantity_delivered_kg | Quantity Delivered Kg | Float | Yes |  |
| quality_grade | Quality Grade | Select | No | Grade A, Grade B, Grade C, Rejected |
| purchase_price_per_kg | Purchase Price Per Kg | Currency | Yes |  |
| gross_payment | Gross Payment | Currency | No |  |
| loan_recovery_amount | Loan Recovery Amount | Currency | No |  |
| net_payment | Net Payment | Currency | No |  |
| payment_status | Payment Status | Select | No | Pending, Paid, Partial |
| payment_reference | Payment Reference | Data | No |  |

## Farm Calendar

### Farm Activity

Scheduled activity record for farm operations, costs, assignment, and completion.

Links:

| Field | Target |
| --- | --- |
| farm | Farm |
| activity_type | Farm Activity Type |
| project | Project |
| assigned_to | Employee |
| cost_center | Cost Center |

Fields:

| Field | Label | Type | Required | Options or Target |
| --- | --- | --- | --- | --- |
| naming_series | Series | Select | No | FA-.#### |
| activity_title | Activity Title | Data | Yes |  |
| farm | Farm | Link | Yes | Farm |
| activity_type | Farm Activity Type | Link | Yes | Farm Activity Type |
| project | Project | Link | No | Project |
| scheduled_date | Scheduled Date | Date | Yes |  |
| actual_date | Actual Date | Date | No |  |
| status | Status | Select | Yes | Scheduled, In Progress, Completed, Cancelled |
| assigned_to | Assigned To | Link | No | Employee |
| cost_center | Cost Center | Link | No | Cost Center |
| estimated_cost | Estimated Cost | Currency | No |  |
| actual_cost | Actual Cost | Currency | No |  |
| notes | Notes | Small Text | No |  |
| completion_notes | Completion Notes | Small Text | No |  |

### Farm Activity Type

Master record for standard farm activities and their default frequencies.

Links: none.

Fields:

| Field | Label | Type | Required | Options or Target |
| --- | --- | --- | --- | --- |
| activity_name | Activity Name | Data | Yes |  |
| farm_category | Farm Category | Select | Yes | Crop Farming, Poultry, Livestock, Aquaculture |
| default_frequency | Default Frequency | Select | No | Daily, Weekly, Fortnightly, Monthly, Seasonal, As Required |
| description | Description | Small Text | No |  |
| is_active | Is Active | Check | No |  |

## Reports

### Farm KPI Summary

Script report in the Project Costing module for summarized farm KPI metrics.

### Farm Budget Variance Analysis

Script report in the Project Costing module for comparing farm budgeted values against actual values.

