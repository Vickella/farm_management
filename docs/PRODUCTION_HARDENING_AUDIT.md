# Farm Management Production Hardening Audit

## Purpose and scope

This is the working fixes document for the production-hardening pass. It covers every tracked
application file class, all 73 DocTypes (64 parents and 9 child tables), reports, pages, fixtures,
hooks, install/migrate code, scheduled jobs, permissions, accounting flows, tests, and root
maintenance scripts.

Status meanings:

- **Fixed**: implemented in this hardening pass and covered by static regression checks.
- **Open - P0**: blocks a production accounting launch.
- **Open - P1**: required before broad user rollout.
- **Open - P2**: optimization or consolidation after the accounting core is accepted.

## Executive verdict

The app had a sound modular skeleton but was not production-ready at the start of this pass.
The immediate migration failure came from installing transactional Farm BOM examples as fixtures
before their linked Project Type and UOM records existed. More broadly, several forms used free
text or hard-coded Select options for existing masters, migrations overwrote user-maintained
reference data, scheduled automation contained a no-op, most operational DocTypes were restricted
to System Manager, and the IAS 41 to ERPNext general-ledger handoff is incomplete.

The migration blocker, master selection behavior, UOM handling, seed safety, settings validation,
integration authorization, duplicate reminders, activity generation, and budget actual sourcing
have been hardened. The P0 accounting gaps below remain explicit release gates rather than being
hidden behind a production ready claim.

## Installation and migration flow

1. Frappe loads DocType JSON.
2. The app now declares ERPNext as required; Company, Project, Item, UOM, and Account are checked.
3. Agricultural UOM masters are inserted idempotently.
4. Reference fixtures are inserted without overwriting production edits.
5. Transactional Farm BOM examples are excluded from automatic seeding.
6. Livestock/crop masters and managed-item master links are normalized.
7. settings, accounts, and workspace are created idempotently.

### Migration fixes

- **Fixed**: declare `required_apps = ["erpnext"]`.
- **Fixed**: fail with a clear missing-ERPNext message instead of `DocType UOM not found`.
- **Fixed**: exclude `fixtures/farm_bom.json`; it contains site-specific links and was the direct
  source of missing `Project Type: Poultry Production`, `Piece`, and lowercase `kg`.
- **Fixed**: use ERPNext `UOM` Links and seed domain UOMs safely.
- **Fixed**: make seeds insert-only for Farm Type, Crop Type, Pest, and Animal Disease.
- **Fixed**: populate Crop Type/Livestock Species links on legacy managed-item rows.
- **Open - P1**: run clean install, upgrade-from-current-data, migrate-twice, uninstall/reinstall,
  and backup/restore tests inside a real Frappe v15/ERPNext v15 bench.
- **Open - P1**: replace the monolithic `after_migrate` routine with versioned patches in
  `patches.txt` so historical transformations run once and are auditable.

## Complete DocType register and findings

### Farm Setup

| DocType | Relationship / flow | Status |
| --- | --- | --- |
| Farm | Company owner; Employee manager; multi-select Farm Types | Validates land/GPS. P1: add user-permission scoping by farm/company. |
| Farm Type | Parent Farm Type; managed-item child rows | **Fixed** master-backed crop/species selection and legacy normalization. |
| Farm Type Managed Item | Crop Type or Livestock Species plus accounting accounts | **Fixed** master pickers; display name is derived/read-only. |
| Farm Type Multiselect | Child Link to Farm Type | Structurally sound. |
| Crop Type | Farm Type category; yield UOM | **Fixed** UOM Link. P2: add active flag and agronomic defaults. |
| Agriculture Project Type | Farm Type and managed item | **Fixed** dynamic managed-item options plus server validation. |
| Farm Management Settings | Company, warehouse, cost center, accounts, integration secrets | **Fixed** System Manager-only mutation, company/ledger validation, no embedded weather key. |

### Infrastructure and production

| DocType | Relationship / flow | Status |
| --- | --- | --- |
| Farm Field | Farm and Crop Type | Master-backed crop already present. |
| Farm Pen | Farm, Farm Type, Livestock Species | **Fixed** species Link/filter and capacity validation. |
| Farm Pond | Farm, Farm Type, Livestock Species | **Fixed** aquaculture species Link/filter. |
| Fowl Run | Farm, Farm Type, Livestock Species | **Fixed** poultry species Link/filter. |
| Crop Cycle | Farm, Project, Crop Type | **Fixed** free-text crop converted to Link. P1: date/yield validations. |
| Field Management | Farm and Project | P1: replace generic operation Data fields with activity/input masters. |
| Harvest Log | Farm and Project | P1: consolidate with Harvest Transaction or clearly separate operational log from accounting event. |
| Greenhouse Cycle | Farm, Project, Crop Type | **Fixed** free-text crop converted to Link. |
| Climate Control Log | Farm and Project | P1: add acceptable-range validation and alert automation. |
| Greenhouse Harvest Log | Farm and Project | P1: route accounting harvest through Harvest Transaction. |
| Poultry Flock | Farm and Project | P2: overlaps Biological Asset and Livestock Species. |
| Broiler Batch | Farm and Project | P2: overlaps Poultry Flock/Biological Asset. |
| Egg Production Log | Farm and Project | P1: create stock/produce transaction integration. |
| Poultry Infrastructure | Farm and Project | P2: overlaps Fowl Run; define ownership boundary. |
| Fish Batch | Farm, Project, Livestock Species | **Fixed** hard-coded fish Select converted to filtered Link. |
| Pond Management | Farm and Project | P2: overlaps Farm Pond. |
| Water Quality Log | Farm and Project | P1: thresholds, alerts, and species-specific ranges. |
| Fish Feeding Log | Farm and Project | P2: overlaps Feeding Log. |
| Feeding Log | Farm and Project | P1: link feed Item/UOM and capitalize actual stock consumption. |
| Animal Herd | Farm and Project | P2: consolidate with Biological Asset batch model. |
| Cattle Herd | Farm, Project, Livestock Breed | **Fixed** free-text breed converted to Link. |
| Cattle Infrastructure | Farm and Project | P2: overlaps Farm Pen. |
| Breeding Log | Farm and Project | P2: overlaps Livestock Breeding Record. |
| Meat Production Log | Farm and Project | P1: slaughter must invoke harvest/produce inventory flow. |
| Dairy Cow Herd | Farm and Project | P2: consolidate herd concepts. |
| Dairy Infrastructure | Farm and Project | P2: clarify against Farm Pen. |
| Dairy Milking Cycle | Farm and Project | P1: validate cycle dates and output. |
| Lactation Cycle | Farm and Project | P1: link individual/batch animal master. |
| Milk Yield Log | Farm and Project | P1: generate agricultural produce inventory at collection. |
| Goat Herd | Farm and Project | P2: consolidate with Animal Herd. |
| Goat Breeding Log | Farm and Project | P2: consolidate with Livestock Breeding Record. |
| Goat Meat Milk Log | Farm and Project | P1: split meat harvest from milk produce flows. |
| Pig Batch | Farm and Project | P2: consolidate with Biological Asset batch. |
| Farrowing Log | Farm and Project | P1: generate Birth stock movement and individual records. |
| Pig Infrastructure | Farm and Project | P2: consolidate with Farm Pen. |

### Livestock and IAS 41

| DocType | Relationship / flow | Status |
| --- | --- | --- |
| Livestock Species | Farm Type master | Seeded idempotently; source for all animal/species pickers. |
| Livestock Breed | Species master | Filtered by Species in forms. |
| Livestock Individual | Species, Breed, Farm, Pen, Biological Asset, parents/siblings | Good validation base. P1: enforce unique tag and lifecycle/status transitions. |
| Livestock Sibling | Child Link to Livestock Individual | Structurally sound. |
| Livestock Health Event | Individual, Item, Employee, Biological Asset | Capitalizes completed costs. P0: reconcile source accounting to avoid duplicate expense/capitalization. |
| Livestock Breeding Record | Dam, sire, Farm | P1: validate dates, species, outcomes, and birth automation. |
| Animal Stock Entry | Farm transfer, Biological Asset, Species, Breed, Individual, Item | **Fixed** server/client auto-fill of animal, breed, unit, project, farm, and carrying-value rate. |
| Biological Asset | Farm, Farm Type, Project, managed item, Breed, UOM | **Fixed** managed selection/Breed/UOM. P0: ledger balance reconciliation. |
| Biological Asset Capitalization | Asset, Project, Journal Entry | P0: define source-document accounting and prevent double posting. |
| Biological Asset Valuation | Asset and Journal Entry | Movement logic exists. P0: cancellation ordering and posted-value reconciliation tests. |
| Harvest Transaction | Asset, Item, Warehouse, Stock Entry | **Fixed** UOM/company validation and Biological Asset account as the Material Receipt offset. **Open - P0**: prove the resulting Dr Inventory / Cr Biological Asset posting in bench tests. |

### Costing, accounting, contract farming, calendar, disease

| DocType | Relationship / flow | Status |
| --- | --- | --- |
| Farm BOM | Agriculture Project Type, Farm, mandatory Project, Item/UOM rows | **Fixed** project requirement and Item default-UOM enforcement; unsafe examples no longer seed. |
| Farm BOM Item | Item and UOM | Fetches Item name, stock UOM, valuation rate; server validates UOM. |
| Standard Cost Calculation BOM | Project, Item, UOM, cost rows | **Fixed** UOM, quantity, row-total, total-cost, and per-target-unit calculations. |
| Standard Cost Calculation BOM Item | Item and UOM | **Fixed** server-side UOM, quantity, rate, and total validation. |
| Farm Budget | Farm, mandatory Project, optional Farm BOM | **Fixed** planning-only; manual actual/variance fields removed. |
| Farm Budget Item | Item or Expense Account and UOM | **Fixed** requires a transaction mapping. |
| Budget Forecasting | Project, Farm BOM, expense rows | **Fixed** year, Project/BOM, duplicate month/account, and total validation. |
| Budget Forecasting Expense | Expense Account | Parent validates amount and duplicate account/month rows. P1: company validation. |
| Farm Cashbook | Farm, Project Type, Project, Journal Entry, entry rows | Functional journal creation. P1: add cancel hook and duplicate-JE guard. |
| Farm Cashbook Entry | Debit/Credit Account, Project, Cost Center | Validates through parent. |
| Contract Farming Agreement | Farmer, Farm, Project, sponsor, Crop Type, inputs | Two-direction model present. P0: complete receiving-contract liability flow. |
| Contract Farming Input | Item and UOM | Table model implemented. P1: enforce Item UOM and valuation source server-side. |
| Input Loan Disbursement | Agreement, Farmer, input rows, Journal Entry | Table/rollup implemented. P0: reconcile stock issue and accounting clearing entry. |
| Harvest Recovery | Agreement, Farmer, UOM, Journal Entry | **Fixed** generic quantity/UOM/rate fields with legacy kg migration. P0: connect purchase/stock documents. |
| Outgrower Farmer | primary Crop Type | Master-backed. P1: party/address integration and duplicate identity checks. |
| Farm Activity Type | frequency/category master | Drives scheduler. |
| Farm Activity | Farm, type, Project, Employee, Cost Center, Asset | **Fixed** recurring generation and duplicate avoidance. P1: cancellation of capitalization. |
| Pest | pest reference master | Insert-only seed; user edits preserved. |
| Animal Disease | disease reference master | Insert-only seed; user edits preserved. |
| Disease Incident | Farm, Asset/animal/field, Pest/Disease, Employee | Good conditional requirements. P1: lifecycle, assignment, notifications. |

## Reports and pages

- Biological Asset Register: **Fixed** Farm permission filtering; P1 add company and reconciliation columns.
- Animal Stock Ledger: **Fixed** Farm permission filtering; P1 prove opening/running balances and
  target-farm transfer handling with fixtures.
- Farm Budget Variance Analysis: **Fixed** actuals now come from submitted Purchase Invoice Item
  project/item values or GL Entry project/expense-account values within the budget period.
- Farm KPI Summary: **Fixed** permission-aware farm listing and grouped aggregate queries replace
  per-farm N+1 queries.
- Contract Farming Statement: **Fixed** Farm permission filtering; P1 verify both contract directions.
- Farm Weather page/API: **Fixed** permission-aware farm listing, configured secret only, explicit timeout.
- Agri GPT page/API: **Fixed** role gate, feature flag, farm permission, input bounds. P1 add provider/model
  configuration, audit consent, rate limits, and agricultural safety disclaimer.

## File-by-file class review

- `hooks.py`: dependency, Project JS, document events, and scheduler reviewed and hardened.
- `install.py`: idempotency, dependency order, fixtures, master normalization, account/workspace setup reviewed.
- `patches.txt`: empty; versioned migration work remains P1.
- `modules.txt`: all modules represented.
- Controllers (`*.py`): all non-empty controllers inspected; many generated operational controllers are
  still `pass` and are identified in the DocType register.
- Client scripts (`*.js`): master queries, fetches, calculations, and empty generated scripts reviewed.
- DocType JSON: all 73 parsed; field order, relationships, UOMs, master-like fields, permissions, and child
  tables inventoried.
- Reports/pages: all Python/JS/JSON files reviewed as summarized above.
- Fixtures: all seven fixture files reviewed; Farm BOM removed from migration; reference seeds protected.
- Root `audit.py`, `deep_audit.py`, `apply_fixes.py`, `patch_*.py`, SQL/delete/import/workspace scripts:
  development-only and unsafe for production deployment. P1 move maintained diagnostics under a developer
  command, delete obsolete destructive scripts after owner confirmation, and exclude them from release artifacts.
- `check.py` and `clean_db.py` are untracked user files and were intentionally not modified.
- Documentation and packaging files reviewed; P1 update README with exact supported Frappe/ERPNext versions,
  backup procedure, scheduler/worker requirements, and rollback instructions.

## Production release gates

### Open - P0

1. Prove IAS 41 ledger reconciliation: every Biological Asset carrying-value change must equal GL movement.
2. Replace/complete harvest accounting so inventory recognition and biological-asset derecognition balance.
3. Route live-animal Purchase and Sale through standard Purchase Invoice/Sales Invoice and derecognize the
   carrying amount exactly once; remove misleading unused Journal Entry fields.
4. Reconcile Stock Entry material issues, health/activity costs, and capitalization to prevent double counting.
5. Complete both directions of contract-farming accounting and stock movement.
6. Run full clean/upgrade/migrate-twice/runtime tests in a Frappe v15 + ERPNext v15 bench with a test company.

### Open - P1

1. Permission matrix for Farm Manager, Farm Worker, Agronomist, company, and farm-level access.
2. Meaningful controller tests; current generated tests mostly verify metadata/imports.
3. Versioned patches and rollback documentation.
4. Cancel/amend/idempotency tests for every document that creates another submitted document.
5. Consolidate duplicate operational models and define a single source of truth.
6. Query profiling and indexes after realistic data-volume tests.
7. CI for JSON contracts, Python lint/format, JavaScript lint, bench migration, and Frappe tests.

## Verification commands

```bash
python -m unittest farm_management.tests.test_repository_contracts -v
python -m compileall -q farm_management
bench --site <test-site> install-app erpnext
bench --site <test-site> install-app farm_management
bench --site <test-site> migrate
bench --site <test-site> migrate
bench --site <test-site> run-tests --app farm_management --verbose
```

Do not approve production launch until all P0 gates pass against a restored copy of production-like data.
