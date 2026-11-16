# Navigation audit — 16.2.1

Base: `version-16-hotfix`. Native schemas/controllers reviewed against Frappe version-16 commit `49789a1711d4dde2be9c6888efe35651465f4b64`. These are source-authored exports, not developer-site exports.

## Navigation coverage

App entry and Dock are reused; Dock opens the module Sidebar. All standalone DocTypes and reports appear in both Sidebar and Workspace. Child tables remain accessible only inside their parent forms. Settings are grouped separately; underlying permissions remain authoritative.

| Group | Targets | Workspace | Sidebar |
| --- | --- | --- | --- |
| Daily Operations | Metal Intake, Metal Assay, Refining Batch, Refining Operation | Yes | Yes |
| Settlement & Pricing | Metal Price Fixing, Metal Purchase Settlement | Yes | Yes |
| Traceability & Reconciliation | Metal Lot, Refining Batch Reconciliation, Metal Exception | Yes | Yes |
| Reference Masters | Metal Type, Assay Method | Yes | Yes |
| Vault & Custody | Metal Custody Transfer, Metal Custody Count, Metal Bar Register | Yes | Yes |
| Toll Refining | Toll Refining Agreement, Toll Refining Job, Metal Release Authorization | Yes | Yes |
| Sales & Export | Metal Export Shipment | Yes | Yes |
| Operational Reports | Metal Intake Traceability, Refining Yield and Variance, Metal Custody and Bars | Yes | Yes |
| Settings & Administration | Metal Refinery Settings, Metal ERPNext Posting Profile | Yes | Yes |
| Dashboard | Metal Refinery Operations | Dashboard shortcut | Dashboard link |

Excluded child tables (parent-owned, no independent navigation): Metal Assay Result, Metal Custody Count Item, Metal Custody Transfer Item, Metal ERPNext Item Mapping, Metal Export Checklist Item, Metal Intake Measurement, Metal Intake Sample, Metal Operation Cost, Metal Release Line, Metal Settlement Charge, Refining Batch Input, Refining Batch Output, Toll Refining Rate.

## Analytics definitions

All metrics count parent documents once, across all dates and companies allowed by the current user’s document/user permissions. No currency amounts or historical trends are inferred. Cards drill into their source list with the same filters; charts group current records. Framework standard Document Type cards and Group By charts use `frappe.get_list`; no custom Chart Source is needed.

| Metric | Source | Formula / filters | Display |
| --- | --- | --- | --- |
| Draft Toll Refining Jobs | Toll Refining Job | Count; [["docstatus","=",0]] | Card, Dashboard, Workspace |
| Open Metal Exceptions | Metal Exception | Count; [["docstatus","=",0]] | Card, Dashboard, Workspace |
| Open Metal Intakes | Metal Intake | Count; [["docstatus","=",0]] | Card, Dashboard, Workspace |
| Pending Custody Transfers | Metal Custody Transfer | Count; [["docstatus","=",0]] | Card, Dashboard, Workspace |
| Pending Metal Assays | Metal Assay | Count; [["docstatus","=",0]] | Card, Dashboard, Workspace |
| Pending Metal Releases | Metal Release Authorization | Count; [["docstatus","=",0]] | Card, Dashboard, Workspace |
| Refining Batches | Refining Batch | Count; [["docstatus","!=",2]] | Card, Dashboard, Workspace |
| Assays by Status | Metal Assay | Count; [["docstatus","!=",2]]; group by assay_status | Chart, Dashboard, Workspace |
| Refining Batches by Status | Refining Batch | Count; [["docstatus","!=",2]]; group by status | Chart, Dashboard, Workspace |
| Toll Refining Jobs by Metal | Toll Refining Job | Count; [["docstatus","!=",2]]; group by metal_type | Chart, Dashboard, Workspace |

“Open” / “Pending” cards mean draft documents (`docstatus=0`); Refining Batches includes drafts and submitted documents. Charts now exclude cancelled documents. No card definitions changed.

## Verification matrix

| Surface | Source | Installed record | Role / rendered view |
| --- | --- | --- | --- |
| App entry + Dock | Reused, target checked | Pending | Pending |
| Sidebar | Updated; all targets checked | Existing record found; update pending deployment | Pending |
| Workspace | Updated; blocks and collections checked | Existing record read; update pending deployment | Pending |
| Seven Number Cards | Reused; fields, filters, standard flags checked | Pending | Pending |
| Three Charts | Updated cancellation filters; grouping fields checked | Pending | Pending |
| Chart Sources | Not applicable: native Group By aggregation | Not applicable | Not applicable |
| Dashboard | Reused; module Dashboard export path and all dependencies checked | Existing record found | Pending |

Local validation: `python scripts/validate_app_sources.py`, Python compilation and `git diff --check`. The validator now rejects missing standalone DocTypes/reports, duplicate or unresolved targets, missing dashboard navigation, mismatched Workspace blocks, incorrect report route metadata, non-standard analytics and invalid field references. No Frappe bench is installed here.

The live connector returned Workspace data and found Sidebar and Dashboard, then returned connection errors. This prevents updated-record, role and browser verification. Keep the PR draft until the following checks pass.

## Deployment and acceptance

1. Deploy the PR commit to the development bench and run `bench --site dev16-metal-refinery.aakvaerp.com migrate`. Confirm app version 16.2.1.
2. Verify Dock `metal_refinery_tz`, Sidebar/Workspace `Metal Refinery TZ`, Dashboard `Metal Refinery Operations`, and every card/chart above exist with matching references.
3. Open the app Overview, Operations Dashboard shortcut, each operational report, and Settings & Administration. Validate Workspace blocks and Dashboard View separately.
4. Check Stock User, Stock Manager and System Manager accounts. The posting profile is restricted by its existing System Manager / Stock Manager / Accounts Manager DocType permissions. No new roles or permission grants are introduced.
5. Check a controlled draft/submitted/cancelled record set: cards count drafts (or non-cancelled batches); chart totals exclude cancelled records and respect user permissions. Verify counts against the corresponding filtered lists.
6. Confirm existing custom Dock/Sidebar arrangements remain intact. No reset, fixture rewrite or migration patch is introduced.

Central maintenance config currently lists only `av_tools`; this repository uses its existing Frappe application static-check workflow. Central CI is not claimed. Rollback by reverting this PR and migrating; no business data or DocType schema is changed.
