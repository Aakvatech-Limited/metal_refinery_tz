# ERPNext financial and stock bridge — controlled draft generation

## Status
**Source code only. This integration is NOT yet deployed, bench-tested, or enabled for live posting.**

The prior Metal Refinery TZ controllers only calculated operational quantities. They did **not** create ERPNext stock or financial documents. This change introduces guarded draft preparation, not an accounting approval engine. Existing operational records are not backfilled.

### Configuration: Metal ERPNext Posting Profile
Create **one profile per Company** as a System Manager/Accounts Manager. It requires an explicit company Cost Center, compatible Accounts, and approved ERPNext Item mappings:
- `metal_item_mappings` — one row **per Metal Type** mapping its Raw Metal Stock Item, optional Finished Metal Item, and optional Residue Item. Stock UOM must equal the operational transaction UOM.
- `toll_service_item` — non-stock service item.
- `expense_account` — charge operating costs to the approved expense account.
- `income_account` — credit tolling revenue to the approved income account.
- `receipt_warehouse`, `wip_warehouse` — matching company warehouses.
- Optional `project` — used to tag relevant ERPNext rows.
- `auto_create_drafts=0` **by default**. Only enabling it explicitly causes new operational submissions to generate ERPNext drafts.

## Controlled document workflows

| Operational source | Trigger | ERPNext document prepared | Stock/GL impact |
|---|---|---|---|
| Submitted Metal Purchase Settlement | on_submit | **Purchase Receipt — Draft** | None until authorized PR submission |
| Submitted linked Purchase Receipt | on_submit hook | **Purchase Invoice — Draft**, linked to PR item | None until authorized PI submission; PI `update_stock=0` |
| Submitted Toll Refining Job | on_submit | **Sales Invoice — Draft**, non-stock service item | None until authorized SI submission |
| Submitted Refining Batch with cost rows | on_submit | **Purchase Invoice — Draft** per supplier, non-stock cost items | None until authorized PI submission |
| Submitted company-owned Refining Batch | on_submit, only if stock receipt is already submitted and WIP is configured | **Material Transfer Stock Entry — Draft** | None until authorized Stock Entry submission |
| Customer-owned metal | any | No company-owned stock receipt/transfer | No company stock valuation |

### Accounting and costing semantics
- Purchase Receipt metal quantity uses the **intake gross metal weight** (net-of-tare), NOT fine assay weight. Its unit rate uses settlement amount divided by intake weight, but **only when settlement deductions are zero**. Deductions and charges need defined GL treatment and cannot be silently netted into inventory.
- Purchase Invoice is generated **after the linked Purchase Receipt is submitted**, with `purchase_receipt` and `pr_detail` links, and `update_stock=0` to avoid duplicate stock posting.
- Toll Sales Invoice is non-stock with `update_stock=0`, service fee, company, customer, Cost Center, Project and explicit income Account if configured.
- Refining operating costs are entered in a full-width `Metal Operation Cost` child grid with Supplier, non-stock Item, Quantity, Rate, Cost Center and Project. On batch submission, one draft Purchase Invoice per supplier is created and linked back to each cost row.
- **Operating costs are expensed, not capitalized to WIP or finished bullion inventory.** Capitalization requires an approved valuation/burden policy, production BOM/process item mappings and treatment of multiple metal outputs.
- Auto-generated drafts are linked to operational documents and contain source references in remarks/line descriptions; reruns do not intentionally create a second draft where links already exist. Transactional uniqueness under concurrent requests still needs real integration/load testing.
- Read-only generated links on settlement, batch and toll job prevent casual editing via Desk. Cancellation of operational records with **any existing** linked ERPNext document is blocked pending an explicit unlink/reconciliation; this prevents orphan drafts as well as submitted postings.
- No automatic ERPNext document submission. There is no background job that posts journals, tax or stock without human action.

### Not implemented
- Finished bullion Stock Entry manufacture/repack and residue accounting.
- Multi-metal/by-product allocation and recoverable loss valuation.
- Customer-owned metal in ERPNext Stock Ledger (custody records remain separate).
- Batch-specific ERPNext Batch Numbers and serialized bar stock.
- Multiple UOM conversions and exchange rates.
- Automatic tax/VAT/WHT/excise calculation configuration and deduction GL mappings.
- Stock cost capitalization and variance posting.
- Historical backfill of pre-existing operational documents.
- Draft generator reconciliation dashboard and concurrency locks.

### Essential UAT before enabling
1. Create valid stock and service Items with company defaults and correct stock UOM.
2. Configure expense/income accounts and Cost Center for the chosen Company.
3. Verify default profile is **disabled**; new operational submissions must generate no ERPNext drafts.
4. Enable on a disposable v16 site and run a new **zero-deduction** supplier settlement: verify exactly one Draft PR, then manually submit PR and verify exactly one Draft PI tied to its PR item.
5. Run a new toll job: verify exactly one Draft SI, correct service fee and income account, and no stock impact.
6. Run company-owned batch with operating cost rows: verify supplier PI rows, per-row Cost Center and Project, and source links.
7. Check ownership mismatch, duplicate attempt, invalid account/company, no PR stock balance, wrong UOM, and cancellation with submitted accounting documents.
8. Review Purchase Receipt taxes, purchase and sales invoice tax templates, default payable/receivable accounts and posting date/period validity.
9. Confirm all new forms use <=3 columns and standalone full-width child grids.
10. Verify no Stock Ledger Entry or GL Entry exists **before submitting the corresponding ERPNext document**.

Deployment: merge PR into `version-16-hotfix`, pull updated app code, run `python apps/metal_refinery_tz/scripts/validate_app_sources.py` and `bench --site dev16-metal-refinery.aakvaerp.com migrate`. Keep the new profile disabled until these tests pass.

## Implementation gate
**Nothing runs until a company Posting Profile is created and explicitly enabled.** On test sites with previously submitted operational documents, there is no automatic backfill; create NEW source documents after enabling the profile. Existing test data remains unchanged.

## Metal-specific mapping
Configure one item-mapping row per metal. Never reuse a gold stock item for silver or other metals. Standard ERPNext stock items, stock UOM and account defaults must be configured before attempting any Purchase Receipt or WIP Stock Entry draft. Finished-metal and residue mappings are reserved for a subsequent validated manufacture/valuation integration, not used for automatic finished-goods posting in this PR.
