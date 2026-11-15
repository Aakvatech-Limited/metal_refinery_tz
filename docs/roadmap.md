# Metal Refinery TZ delivery roadmap

## Phase 1 — Foundation
- [x] Frappe v16 app metadata, modules, package, CI
- [x] `version-16` and `version-16-hotfix` branches
- [ ] Install/migrate on a live Frappe/ERPNext v16 test site

## Phase 2 — Intake, assay and settlement
- [x] Metal Intake/Measurements/Samples and Metal Lot
- [x] Metal Assay/Results, Price Fixing and Purchase Settlement
- [x] Opt-in *draft* Purchase Receipt / Purchase Invoice / toll Sales Invoice generation bridge
- [ ] Automatic submission and finalized stock/GL posting, with approved valuation and tax rules

## Phase 3 — Refining
- [x] Refining Batch, Inputs/Outputs, Refining Operation and Reconciliation
- [x] Mass balance and Metal Exception checks
- [ ] Multi-metal recovery, partial lot allocations, full ERPNext production integration

## Phase 4 — Vault, custody, tolling and export (this PR)
- [x] Whole-lot Metal Custody Transfer and physical Metal Custody Count
- [x] Metal Bar Register checked against produced fine-metal output
- [x] Toll Refining Agreement, Rate and Toll Refining Job
- [x] Metal Release Authorization and customer-owned export shipment documentation
- [x] Sidebar/Workspace, Dashboard Chart, Number Cards and Dashboard updated
- [ ] Real Frappe v16 deployment, workflow and user-role verification
- [ ] Partial lot/metal allocation engine and customer-owned metal custody ledger
- [ ] Automatic ERPNext invoicing/stock accounting and export integrations

## Phase 5 — Reporting and readiness
- [x] Initial operational count cards and grouped charts
- [x] Intake traceability, batch yield/variance, and custody/bar operational reports
- [ ] Financial valuation and GL reconciliation reports (await ownership and posting specification)
- [x] Per-metal ERPNext Item mappings, operation-cost allocation tags and draft WIP transfers
- [ ] Finished bullion manufacture/repack stock entries and capitalized operating costs
- [ ] Workflow/permission review for custody and release, two-party authenticated handover
- [ ] Site UAT, multi-user concurrency, cancellation and regression tests
