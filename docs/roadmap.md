# Delivery roadmap

## Stage 0 — Foundation (this change)
- [x] Initialize Frappe application and v16 compatibility metadata
- [x] Create version-16 and version-16-hotfix branches
- [x] Add Python package, module markers, asset, docs, basic CI
- [ ] Bench installation and migration test on a real Frappe/ERPNext v16 site

## Stage 1 — Metal intake and assay
- [ ] Masters: Metal Type, Metal Form, Purity Standard, Assay Method and Settings
- [ ] Metal Intake and child measurement/sample rows
- [ ] Metal Assay, result and retest controls
- [ ] Metal Lot ownership/custody linkage
- [ ] Purchase Settlement and pricing controls
- [ ] Corresponding permissions, workflows and tests

## Stage 2 — Refining
- [ ] Refining Batch, input, output and operation records
- [ ] Fine-metal recovery/variance and reconciliation
- [ ] ERPNext BOM, Work Order, Stock Entry integrations
- [ ] Approval and exception rules

## Stage 3 — Custody, tolling and commerce
- [ ] Vault transfers and counts
- [ ] Bar register, owned vs customer metal
- [ ] Toll Refining Agreement/Job and service fees
- [ ] Controlled metal release and export authorization

## Stage 4 — Native v16 navigation and analytics
- [ ] Standard Dock and app Desktop registration
- [ ] Workspaces and module Sidebars, permission-aware
- [ ] Number Cards, Dashboard Charts and Chart Sources
- [ ] Executive, Operations, Custody and Finance Dashboards
- [ ] Operational and GL reconciliation reports

## Stage 5 — UAT
- [ ] Precision and conversion test cases
- [ ] Lot split/merge and ownership scenarios
- [ ] Idempotent transaction/cancellation tests
- [ ] Operator, manager and admin permissions
- [ ] Site migration and real Desk navigation checks
