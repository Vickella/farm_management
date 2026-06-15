# Farm Management

Farm Management is a Frappe/ERPNext v15 custom app for agricultural ERP workflows: farm setup, infrastructure, projects, calendars, disease intelligence, biological assets, BOMs, budgets, contract farming, AI assistance, and analytics.

## Installation

1. Put this repository at `apps/farm_management` in a Frappe bench.
2. Install the Python package into the bench environment with `bench setup requirements` or `./env/bin/pip install -e apps/farm_management`.
3. Run `bench --site <site> install-app farm_management`.
4. Run `bench --site <site> migrate` to load DocTypes, custom fields, and fixtures.

If a site already lists `farm_management` in `sites/apps.txt` but the package was not installed in the bench virtualenv, Frappe will raise `ModuleNotFoundError: No module named 'farm_management'`. Re-run step 2, then restart the bench processes.

## Configuration

Open **Farm Management Settings** and configure biological asset, fair value gain/loss, default cost center, and AI provider credentials.

## Modules

- Farm Setup: Farm, Farm Type, Crop Type.
- Farm Infrastructure: fields, ponds, pens, and fowl runs.
- Farm Projects: ERPNext Project agriculture custom fields and validation hooks.
- Farm Calendar: scheduled activities and operational task generation.
- Disease Intelligence: pests, animal diseases, and incidents.
- Biological Assets: IFRS 41 fair value tracking and harvest stock integration.
- Farm BOM: production templates and input costing.
- Project Costing: budgets, variance calculations, and reports.
- Contract Farming: outgrowers, agreements, input loans, and recoveries.
- Agri AI: AgriGPT desk page and backend API.

## Tests

```bash
bench --site <site> migrate
bench --site <site> run-tests --app farm_management --verbose
python -m flake8 farm_management/ --max-line-length=120 --exclude=__pycache__,migrations
```

## Known Limitations

- Account creation is intentionally conservative and does not mutate ERPNext charts of accounts automatically.
- Stock Entry warehouse selection should be adapted to each deployment's warehouse strategy.
- AI responses require a configured API key.
