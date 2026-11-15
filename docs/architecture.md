# Proposed architecture

## Boundaries
Metal Refinery TZ is the operational industry layer. Reuse ERPNext Item, Company, Supplier, Customer, Warehouse, BOM, Work Order, Stock Entry, Purchase Invoice, Sales Invoice, Asset, Payment Entry and GL.

- Legal ownership is not the same as physical custody.
- Customer-owned metal must not be automatically recognized as company inventory.
- Mass balance is per metal, per unit and per assay/fineness basis.
- Monetary analytics require a company/currency basis.
- Final approval does not erase anomalies.
- Source records should retain amendment and audit history.

## Core controllers (planned)
- `MetalIntake`: receipt metadata, weights, lot traceability and ownership.
- `MetalAssay`: purity tests, provisional/final results, retests.
- `MetalPurchaseSettlement`: metal pricing, deductions and payable calculation.
- `RefiningBatch`: inputs, operations, outputs and ERPNext manufacturing links.
- `RefiningBatchReconciliation`: fine-metal mass balance and variance approval.
- `TollRefiningJob`: customer-owned metal and service fees.
- `MetalCustodyTransfer`: two-party release/receipt acknowledgements.
- `MetalException`: unresolved discrepancies and exception reviews.

## Integration boundaries
Accounting and inventory posting must use ERPNext APIs and remain idempotent. Share business aggregation services across reports, cards and Dashboard Chart Sources. Prefer Frappe Query Builder and ORM over raw SQL.

## Navigation
For Frappe v16.50+, introduce the app entry in `add_to_apps_screen` together with an actual standard Workspace route, and export a module Sidebar and Dock from a development-mode v16 site. Do not ship dead links, fabricated navigation JSON, or a fixture that overwrites site-specific arrangements.

## Acceptance checkpoints
1. Minimal app installs and migrates on a clean Frappe/ERPNext v16 test site.
2. Core DocTypes load with validated permissions.
3. Intake-to-refining traceability and ownership invariants pass tests.
4. Dashboard Source (.json, .py, .js), Chart, Number Card, Dashboard and Workspace records exist and render for relevant users.
