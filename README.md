# Farm Management

Farm Management is a focused Frappe/ERPNext v15 app for farm setup, agricultural projects, field and livestock operations, IAS 41 biological assets, harvest inventory, budgeting, and farm accounting.

## Installation

1. Put this repository at `apps/farm_management` in a Frappe bench.
2. Install the Python package into the bench environment with `bench setup requirements` or `./env/bin/pip install -e apps/farm_management`.
3. Install ERPNext first: `bench --site <site> install-app erpnext`.
4. Install Farm Management: `bench --site <site> install-app farm_management`.
5. Run `bench --site <site> migrate` to load DocTypes, custom fields, and fixtures.

Farm Management declares ERPNext as a required app and will stop with a clear dependency error
if ERPNext's Company, Project, Item, UOM, or Account DocTypes are unavailable. Farm BOM examples
are not installed automatically because Project, Item, and UOM links are site-specific.

If a site already lists `farm_management` in `sites/apps.txt` but the package was not installed in the bench virtualenv, Frappe will raise `ModuleNotFoundError: No module named 'farm_management'`. Re-run step 2, then restart the bench processes.

## Configuration

Open **Farm Management Settings** and configure the default company, cost center, harvest warehouse, biological-asset sale accounts, and automation flags.

## Modules

- Farm Setup: farms, Farm Types, produce, Crop Types, species, breeds, and Project profiles.
- Farm Infrastructure: fields, pens, and fowl runs.
- Field Operations: activities, Item requirements, and harvest logs.
- Livestock: individual animals, breeding, health events, and stock movements.
- Biological Assets: IAS 41 capitalization, valuation, harvest transfer, and reconciliation.
- Planning and Costing: Farm BOMs, budgets, variance analysis, and KPI reporting.
- Accounting: Farm Cashbook and standard ERPNext financial reports.
- Health and Biosecurity: pests, animal diseases, and incidents.

## Tests

```bash
bench --site <site> migrate
bench --site <site> run-tests --app farm_management --verbose
python -m flake8 farm_management/ --max-line-length=120 --exclude=__pycache__,migrations
python -m unittest farm_management.tests.test_repository_contracts -v
```

## Known Limitations

- Configure and verify all generated biological-asset accounts before live posting.
- Harvest currently closes the whole crop Biological Asset; staged or partial harvests require further work.
- Validate stock, GL, cancellation, and amendment flows on a staging site before production use.
