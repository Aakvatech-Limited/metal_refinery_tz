# Operational reporting (v16)

Three **standard Frappe Script Reports** are added to the Metal Refinery TZ module. These reports use Frappe ORM (`frappe.get_all`) without SQL and are linked through the app Sidebar and Workspace.

## Reports
1. **Metal Intake Traceability** — submitted intake → owner and lot → latest non-superseded approved assay → optional settled purchase → linked submitted refining batch. A lot used in multiple batches produces one row per batch.
2. **Refining Yield and Variance** — submitted batches with fine-metal input, finished recovery, residue, process loss, samples/closing WIP and reconciled difference. Recovery is finished fine metal divided by input fine metal.
3. **Metal Custody and Bars** — operational location snapshot of intake lots and registered bars, including ownership, customer, weight and release status. Lots and bars may represent different stages of the same material, **so the report MUST NOT be summed as a combined metal inventory balance**.

### Operational constraints
- All quantities retain their transaction UOM. Filter or group per metal and UOM; the report does not perform gram/kg conversions.
- Assay purity is applied to the **full intake** as an estimate; assay sample fine-metal quantity is not incorrectly treated as total received fine metal.
- Only submitted intakes and batches are included in traceability/yield.
- This release makes no Stock Ledger Entry, GL Entry, valuation or accounting assertions.
- Records flagged as TEST are synthetic; report filters may be used to restrict to test companies/parties.
- No additional DocTypes are introduced: the previously approved maximum-three-column sections and full-width child-grid layouts remain unchanged.

### UAT checklist
- Validate all three reports load from Desk and Sidebar for Stock User, Stock Manager and System Manager.
- Filter by Company, Metal, Ownership, Warehouse and date where applicable.
- Confirm MINT-2026-00001 traces to RBAT-2026-00010 on dev16 test site.
- Confirm RBAT-2026-00010 and RBAT-2026-00011 show zero unaccounted fine metal.
- Confirm company-owned and customer-owned material remain differentiated.
- Confirm the custody snapshot does **not** imply summable on-hand stock.
- Check access control, report visibility, performance on growing datasets and absence of permission bypass before production.
