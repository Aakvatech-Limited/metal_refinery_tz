# DocType form and child grid layout

All 30 standard DocTypes (19 parent forms and 11 child tables) have layout metadata.

## Form design rules

- Related business fields appear in clearly labeled sections (identity, parties, custody, pricing, measurement, approval, integration, notes).
- A section contains **one to three columns**, never more.
- Every child Table field appears in an independent, full-width section (for example: Metal Intake Measurements and Samples, Refining Batch Inputs and Outputs).
- Read-only calculated fields remain read-only; required flags and fieldnames are preserved.
- Multi-line remarks remain in dedicated sections for readability.
- Layout adds only Frappe Section Break and Column Break fields; no changes to business logic, validation, or DB field types.

## Child-table inline grid columns

| Child Table | Columns visible without expanding row |
| --- | --- |
| Metal Assay Result | Metal Type, Purity %, Fine Weight |
| Metal Custody Count Item | Metal Lot, Recorded Weight, Counted Weight, Variance |
| Metal Custody Transfer Item | Metal Lot, Transfer Weight, UOM |
| Metal Export Checklist Item | Requirement, Evidence Reference, Verified, Verified By |
| Metal Intake Measurement | Measurement Type, Gross Weight, Tare Weight, Net Weight |
| Metal Intake Sample | Sample ID, Sample Weight, UOM |
| Metal Release Line | Bar, Gross Weight, Fine Weight, UOM |
| Metal Settlement Charge | Description, Amount |
| Refining Batch Input | Metal Lot, Input Weight, Purity %, Fine Weight |
| Refining Batch Output | Output Type, Gross Weight, Purity %, Fine Weight |
| Toll Refining Rate | Metal Type, Rate / Unit, UOM, Minimum Fee |

Other child fields remain available when a grid row is expanded. Display widths use Frappe's `columns` metadata and stay within its 10-unit grid limit.

## Verification

The static `scripts/validate_app_sources.py` check enforces the three-column limit, section boundaries, field order, grid visibility and width budget, and full-width child tables.

After the PR is merged to `version-16-hotfix`, update the code on the dev bench, run migration and clear cache. Review Metal Intake, Refining Batch, Toll Refining Job, Custody Count, Export Shipment and a few child-row expand dialogs in the actual Desk UI. Also check for existing site Property Setters or Custom Fields that override standard form layout. Do not overwrite customer-specific customizations just to force display.

This work is a code-level export, not proof of rendered UI or site deployment.
