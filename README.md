# Metal Refinery TZ

Frappe/ERPNext v16 companion application for operational traceability in precious-metal refineries.

## Functional coverage
Metal Intake, Assay and Price Fixing; Purchase Settlement; Refining Batch multi-round traceability, repeated output-lot assays, and fine-metal reconciliation including palladium byproduct recovery; Vault Custody Transfer and Count; Metal Bar Register; Toll Refining Agreement and Job; controlled Metal Release Authorization; and Metal Export Shipment with evidence checklist.

Navigation includes the app Desktop entry, standard Dock, Sidebar, Workspace, initial Number Cards, Dashboard Charts and Operations Dashboard.

## Installation

```sh
bench get-app --branch version-16-hotfix https://github.com/Aakvatech-Limited/metal_refinery_tz.git
bench --site YOUR_SITE install-app metal_refinery_tz
bench --site YOUR_SITE migrate
bench --site YOUR_SITE clear-cache
```

For an existing installation, pull the latest app code before migrating. Phase 4 features appear on `version-16-hotfix` only **after the Phase 4 PR is merged**.

## Safety / not yet ready for production
- No automated ERPNext inventory or accounting postings, invoices, payments or customs-system submissions.
- Whole-lot custody transfers and single-customer-intake toll processing only.
- Bar registration and release are informational custody controls, not an accounting/stock ledger.
- Export requirement checklist is configurable evidence, not a claim of statutory approval.
- Real installation, unit and user-role integration tests remain to be completed.

See [Stage 4 guide](docs/stage4-custody-tolling-export.md) and [Roadmap](docs/roadmap.md).

Application version: `16.2.2`.
