# Metal Refinery TZ

Frappe and ERPNext **v16** companion app for precious-metal refinery operations.

## Status
Foundation initialized. Business DocTypes, controllers, role permissions, standard Dock/Sidebar/Workspace records, charts, number cards and dashboards are **planned, not yet implemented**. Do not treat the foundation as a production refinery solution.

## Business domains
- Metal intake, assay and purchase settlement
- Refining batches, yields, loss and fine-metal reconciliation
- Customer-owned metal, toll refining and custody
- Vault operations, bars and inventory traceability
- Export compliance and management analytics

ERPNext remains authoritative for company-owned inventory valuation, purchase/sales documents and GL postings. Physical custody is distinct from legal ownership.

## Install
Use a **Frappe/ERPNext v16 bench**, then:

```bash
bench get-app --branch version-16-hotfix https://github.com/Aakvatech-Limited/metal_refinery_tz.git
bench --site YOUR_SITE install-app metal_refinery_tz
bench --site YOUR_SITE migrate
```

No domain DocTypes or workflows will be installed by this bootstrap.

## Development
```bash
python -m compileall -q metal_refinery_tz
python -m pip install -e .
```

Development branch: `version-16-hotfix`. Production merge target: `version-16`.
See [architecture](docs/architecture.md) and [delivery plan](docs/roadmap.md).

## Compatibility
See `pyproject.toml` for bounded Frappe/ERPNext v16 dependencies.
