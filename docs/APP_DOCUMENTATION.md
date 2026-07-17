# Farm Management scope

The app deliberately keeps one generic farm workflow:

Farm setup → ERPNext Project → Farm BOM and Budget → Activities and Requirements → Biological Asset or Animal Stock Entry → Valuation → Harvest or Sale → ERPNext stock and accounting.

ERPNext remains authoritative for Company, Project, Item, UOM, Warehouse, invoices, accounts, cost centers, stock, and the General Ledger.

## Retained Project fields

Agriculture Project Type, derived Farm Type, managed crop/animal/species, optional breed, Project quantity and UOM, initial asset cost, Farm, and generated Biological Asset. Project quantity is separate from harvest quantity and harvest Item stock UOM.

## DocType inventory

### Setup

| DocType | Purpose | Fields retained |
|---|---|---|
| Farm | Company-owned operating location. | Name, company, registration, status, manager, location/GPS, land size, irrigation, water, soil, climate, Farm Types. |
| Farm Type | Valid activities and produce. | Name, active, description, managed rows. |
| Farm Type Managed Item | Activity/produce and IAS 41 account mapping. | Activity, dynamic produce, asset, work-in-progress and gain/loss accounts. |
| Farm Type Multiselect | Farm classification row. | Farm Type. |
| Agriculture Project Type | Reusable Project production profile. | Name, Farm Type, default produce, active. |
| Crop Type | Crop/yield master. | Name, category, growth days, expected yield, yield UOM. |
| Farm Management Settings | Minimal defaults and controls. | Company, cost center, harvest warehouse, sale accounts, activity/fair-value flags. |

### Infrastructure

| DocType | Purpose | Fields retained |
|---|---|---|
| Farm Field | Crop field. | Number, farm, status, hectares, crop, soil, irrigation, last harvest. |
| Farm Pen | Livestock capacity. | Number, farm, pen type, Farm Type/species, status, capacity, occupancy/rate. |
| Fowl Run | Poultry capacity. | Number, farm, Farm Type/species, status, capacity, flock size. |

### Planning and operations

| DocType | Purpose | Fields retained |
|---|---|---|
| Farm BOM | Project input/cost plan. | Project type, farm/Project, quantity/UOM, cycle/dates, Item rows, total. |
| Farm BOM Item | One planned input. | Category, description, Item, quantity/UOM, rate, total. |
| Farm Budget | Period budget. | Farm/Project/BOM, dates, status, rows, total. |
| Farm Budget Item | One budget line. | Category, Item/account, description, quantity/UOM, rate, amount. |
| Farm Activity Type | Activity template. | Name, category, frequency, description, active. |
| Farm Activity | Work and optional asset capitalization. | Farm/type/Project, dates/status, employee, cost center, costs, asset and source. |
| Field Management | Crop work requirements. | Farm/Project/date/activity, details, Item rows, total, amended-from. |
| Field Management Requirement | One estimated input. | Item, quantity/UOM, valuation rate, amount. |
| Harvest Log | User harvest entry. | Farm/Project/asset, Item, quantity/stock UOM, fair value, moisture, warehouse, generated documents. |

### IAS 41

| DocType | Purpose | Fields retained |
|---|---|---|
| Biological Asset | Current quantity and valuation state. | Identity/context, Project/produce/breed, quantity/UOM, weight/mortality, cost/fair value and snapshots. |
| Biological Asset Capitalization | Adds controlled cost/quantity. | Asset/date/type, amount/delta, sources, Project, account, Journal Entry, amended-from. |
| Biological Asset Valuation | Dated fair-value measurement. | Asset/date/method, current/previous values, movement, basis, Journal Entry, amended-from. |
| Harvest Transaction | Transfers crop value to inventory. | Farm/company/asset, quantity/UOM, before/after, Item/warehouse, value reduction, Stock Entry, amended-from. |

### Livestock

| DocType | Purpose | Fields retained |
|---|---|---|
| Livestock Species | Species master. | Name, Farm Type, group, active. |
| Livestock Breed | Breed master. | Name, species, active. |
| Livestock Individual | Identifiable animal. | Tag/species/breed/sex, birth/weight, farm/pen/status, acquisition, asset, parents/siblings, physical identity. |
| Livestock Sibling | Sibling link row. | Sibling. |
| Livestock Breeding Record | Mating and birth outcome. | Parents/farm, dates/method, outcome, offspring counts. |
| Livestock Health Event | Animal health work. | Animal/farm/date/type, staff, product/dose/batch, weight/due date, cost, asset source, outcome. |
| Animal Stock Entry | Purchase, sale, transfer, death or issue. | Context, animal classification, quantity/UOM/value, invoice/party/Item, asset adjustments and amended-from. |

### Health and accounting

| DocType | Purpose | Fields retained |
|---|---|---|
| Animal Disease | Disease knowledge master. | Risk flags, symptoms, prevention, schedule, treatment. |
| Pest | Pest knowledge master. | Classification, severity, symptoms, causes, treatments. |
| Disease Incident | Operational incident. | Farm/date/type/severity, references, impact, treatment/cost/loss, resolution. |
| Farm Cashbook | Farm/Project journal interface. | Date/farm/Project, rows, total, description, Journal Entry, amended-from. |
| Farm Cashbook Entry | One debit/credit instruction. | Type, accounts, amount, Project, cost center, description. |

## Reports

Biological Asset Register, Biological Asset GL Reconciliation, Animal Stock Ledger, Farm Budget Variance Analysis, Farm KPI Summary, and standard ERPNext accounting/stock reports.

## Boundary

The current Harvest Transaction closes the entire crop Biological Asset. Partial or staged harvests are not supported yet.
