# Metal Refinery TZ

ERPNext/Frappe v16 companion app for precious-metal intake, assay, settlement, production batches and reconciliation.

## Features in the feature PR
- Metal Intake with measured weights, customer/company ownership and automatic provenance lot
- Metal Assay with sample-linked purity tests and superseding retest support
- Price Fixing and proposed Purchase Settlement calculations
- Refining Batch inputs, outputs, operations, fine-weight balance, and reconciliation
- Metal Exception review with separation of exception creator and approver
- Native v16 app Desktop entry, Dock, Sidebar, Workspace, four count Number Cards, two Group By Dashboard Charts and Operations Dashboard

**Safety:** No automatic Purchase Invoice, Stock Entry, GL or journal postings are implemented. This is not a production-ready metal stock/accounting system until site UAT and posting policy confirmation.

## Installation
```sh
bench get-app --branch version-16-hotfix https://github.com/Aakvatech-Limited/metal_refinery_tz.git
bench --site YOUR_SITE install-app metal_refinery_tz
bench --site YOUR_SITE migrate
bench --site YOUR_SITE clear-cache
```

The feature PR must be merged before these commands include new Phase 2/3 features.

## Development and checks
```sh
python -m compileall -q metal_refinery_tz
bench --site YOUR_SITE run-tests --app metal_refinery_tz
```

See [architecture](docs/architecture.md), [roadmap](docs/roadmap.md), and [Phase 2/3 implementation notes](docs/phase2-phase3-implementation.md).

Package: `metal_refinery_tz`. Target: Frappe/ERPNext v16. Branches: `version-16-hotfix` for staging, `version-16` for production merges.
