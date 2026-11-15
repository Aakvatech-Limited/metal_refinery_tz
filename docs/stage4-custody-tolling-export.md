# Stage 4 — custody, tolling and export controls

## Included
- Metal Custody Transfer with source/destination Warehouse, complete-lot transfer and distinct releasing/receiving users.
- Metal Custody Count with recorded-vs-counted weights, separate reviewer and approved exception for over-tolerance difference.
- Metal Bar Register tied to submitted batch, owner, weight, purity and finished output balance.
- Toll Refining Agreement and weight-based rate/minimum fee schedule; Toll Refining Job for a single customer intake and submitted batch.
- Metal Release Authorization with independently identified authorizer/releaser/receiver and registered bar references.
- Metal Export Shipment with documentation checklist, verified evidence, and links to ERPNext Sales Invoice/Delivery Note where available.
- Standard app Sidebar, Workspace, KPI Number Cards and Operations Dashboard updated.

## Limits and data controls
1. This phase **never posts** stock, Sales Invoices, Journal Entries, Payments, or customs submissions.
2. Custody transfers support entire unprocessed lots only. Partial lot movements, refined output stock ledger and multi-lot toll allocation require a custody ledger in a later phase.
3. Toll jobs allow a batch containing exactly one intake lot. Customer-owned and company-owned metal are never mixed in one toll job.
4. Sale and export authorizations in this phase are **customer-owned toll metal only**; company-owned bullion sales and exports need an independent order/delivery integration.
5. Fee basis is intake gross net weight at the agreement's stated UOM. Purity-adjusted fees, metal-paid fees, tiered pricing and multi-currency valuations need a later rule set.
6. Release must reference registered bars from the job's batch and cannot release the same bar more than once.
7. Registered bars cannot exceed finished fine-metal output from the linked refining batch.
8. The export checklist is user-supplied evidence; statutory applicability must be verified by the client's responsible compliance adviser.
9. Row-level concurrency and full quantity availability over repeated production events require Frappe bench integration tests before production.
10. Site-level customized Dock visibility is not overwritten by this release.

## UAT scenarios
- Company-owned intake is rejected from Toll Refining Job.
- A job with several intake lots is rejected until allocation logic is implemented.
- Warehouse mismatch or mixed UOM in a transfer is rejected.
- Transfer release and receipt performed by the same person is rejected.
- Custody count discrepancy outside tolerance requires approved Metal Exception.
- Bar creation over available finished fine weight is rejected.
- Bar belonging to another customer cannot be released.
- Releasing the same bar twice is rejected.
- Export cannot submit with an unverified or missing evidence row.
- Cancellation of a release with an active export is rejected.
- Intake or batch cancellation with downstream references is rejected.
- KPI Cards, Charts, Sidebar, Dock and Workspace resolve after migration.

## Site deployment
1. Merge the phase PR into `version-16-hotfix`.
2. Update bench app branch, run `bench --site SITE migrate` and `bench --site SITE clear-cache`.
3. Run `bench --site SITE run-tests --app metal_refinery_tz` on a disposable test site.
4. Verify every new DocType in the database and check user-level visibility for Stock User, Stock Manager and System Manager.
5. Inspect data rows and report results before enabling any ERPNext posting or production use.
