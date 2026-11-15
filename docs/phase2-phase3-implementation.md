# Procurement, assay and refining implementation

## Implemented operational flow
1. Configure Metal Type and Assay Method; choose units of measure in ERPNext.
2. Create Metal Intake with an exactly one Final measurement and optional samples; submit.
3. Submission creates a Metal Lot with intake provenance and ownership; **does not post inventory**.
4. Record Metal Assay against a submitted intake sample, approve final results using submission.
5. Create and submit a Metal Price Fixing, then create purchase settlement from approved assay and price. **Does not create Purchase Invoice**.
6. Create Refining Batch with linked Metal Lots, process inputs/outputs, submit after recording output/Loss/WIP.
7. Create Refining Batch Reconciliation. Over-tolerance variance requires a submitted Metal Exception whose approver is not the creator.
8. Refining Operations can reference ERPNext Work Orders / Job Cards, but posting is not automated.

## Important limitations
- One metal type and one ownership classification per refining batch.
- All quantities in the same UOM per transaction; no auto gram/kg conversion.
- Fine quantities computed using Decimal and rounded to six decimals.
- Batch stock allocation checks only submitted batches and is not a substitute for an ERPNext Stock Ledger/custody balance engine.
- Submitted batch output rows describe physical output, including WIP, residue, sample and loss. A positive variance remains unresolved until reconciliation.
- Customer-owned metal remains outside company-owned ERPNext stock by default.
- No Stock Entry, Purchase Invoice, Journal Entry, GL Entry, Work Order creation, or tax posting occurs automatically.
- A standard Frappe/ERPNext v16 bench install and role-based UI validation remain required before production.

## Frappe v16 native navigation included
- App Desktop registration in hooks
- Dock `metal_refinery_tz`
- Sidebar `Metal Refinery TZ`
- Workspace `Metal Refinery TZ`
- Four initial standard Number Cards
- Two standard Group By Dashboard Charts (no custom chart-source bundle required)
- Dashboard `Metal Refinery Operations`

### Post-migrate checks
Execute in `bench --site SITE console`:

```python
for dt, name in [
    ("DocType", "Metal Intake"),
    ("DocType", "Metal Assay"),
    ("DocType", "Refining Batch"),
    ("Dock", "metal_refinery_tz"),
    ("Sidebar", "Metal Refinery TZ"),
    ("Workspace", "Metal Refinery TZ"),
    ("Dashboard", "Metal Refinery Operations"),
    ("Dashboard Chart", "Refining Batches by Status"),
    ("Dashboard Chart", "Assays by Status"),
    ("Number Card", "Open Metal Intakes"),
]:
    print(dt, name, bool(frappe.db.exists(dt, name)))
```

Check both `/desk/metal-refinery-tz` and Dashboard View. If the Dock is missing for existing users, inspect their user/global Dock arrangement; shipping new app Dock records does not guarantee an existing customized arrangement shows it. Check actual site permissions and clear cache after migration.
