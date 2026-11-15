# Delivery roadmap

## Stage 0 — Foundation
- [x] Initialize Frappe application and v16 compatibility metadata
- [x] Create version-16 and version-16-hotfix branches
- [x] Add Python package, module markers, icon, basic CI
- [ ] Bench installation/migration on a live v16 test site

## Stage 1 — Metal intake and assay (this PR)
- [x] Metal Type, Assay Method, Refinery Settings
- [x] Intake measurement/sample child rows and intake-to-lot provenance
- [x] Metal Assay and detailed assay results
- [x] Price Fixing, settlement and charges
- [x] Controller validations and arithmetic tests
- [ ] Site UAT for permissions and end-to-end settlement
- [ ] ERPNext Purchase Invoice/Stock posting (requires approved ownership/accounting policy)

## Stage 2 — Refining (this PR)
- [x] Refining Batch, inputs and outputs
- [x] Refining Operation and Batch Reconciliation
- [x] Fine metal arithmetic, variance exception and approval
- [ ] Integration to BOM/Work Order/Stock Entry posting
- [ ] Multi-metal refining and lot-split traceability
- [ ] Bench integration and posting tests

## Stage 3 — Custody, tolling and commerce (future)
- [ ] Vault transfers, counts, bar register and multiple owners
- [ ] Toll Refining Agreement/Job and fees
- [ ] Controlled metal release and export authorization

## Stage 4 — v16 navigation and initial analytics (included early as requested)
- [x] Standard Dock, Sidebar, Workspace and Desktop registration
- [x] Four initial Number Cards, two Group By charts and Operations Dashboard
- [ ] Test imports, visibility and role-access on live dev-mode v16 site
- [ ] Production metrics, detailed Script Reports and custom charts

## Stage 5 — UAT
- [ ] Mass-balance/precision and workflow tests on installed bench
- [ ] Operator/manager/admin permissions and custom Dock arrangement
- [ ] Real transaction accounting and migration checks
