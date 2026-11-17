# Multi-round refining, repeated assay and palladium UAT

Target branch: `version-16-hotfix`; app version: `16.2.2`.

## Architecture

A Refining Batch is one processing round. Submitted recoverable outputs generate immutable-origin Metal Lots with `source_refining_batch` and `source_output_row`. Each reusable refined lot must have a submitted Metal Assay before it can be consumed by a new batch. `Create Next Round` creates a draft batch; it does **not** post stock or reserve inventory. Refining rounds are numbered from the deepest immediate upstream batch.

An assay of a refined lot records the physical sample ID and its full multi-metal composition. Repeated assays may supersede earlier assays for the same lot/sample. The newest submitted assay governs downstream input purity; only a latest **Final** assay can confirm a finished output.

Metal Type is master-data driven. Palladium (Pd) is seeded by a post-model-sync patch. Gold, silver, palladium and other recovered metals share the same output structure, and their fine-metal contents must be controlled independently.

## Operational workflow

1. Submit intake; obtain the initial Metal Lot and record initial intake assay.
2. Create Round 1 Refining Batch with original lot input, assay-based purity, primary-metal output, residue and recoverable byproducts; submit.
3. Open the output lot from the batch output row and record a new assay on the lot. For further refining, choose the output lot using **Refining Rounds > Create Next Round**. New draft batch has `round_number=2` and an input linked to its latest submitted lot assay.
4. Repeat as many rounds as operationally required. Do not treat an intermediate output as automatically available ERPNext stock.
5. Record **Final** assays on every Finished Metal output lot. Submit the final batch reconciliation to confirm output quality; the reconciliation evaluates measured final assay purity, not the provisional output estimate.
6. Register finished bars only against reconciled, assay-confirmed finished output, subject to fine-metal balance and prior allocations.

**Separate scope:** A mandatory *post-casting bar assay* is intentionally not included in this PR; it will follow after the multi-round workflow is stabilized.

## Downstream dependency: customer post-delivery assay (design hold)

**Status: requirement recorded, implementation deferred.** This is distinct from mandatory post-casting assay/QC on each bar before release. Do not add customer assay DocTypes, ERPNext accounting postings or stock quantity adjustments to this PR until the multi-round refining architecture is finalized and its downstream effects reviewed.

A customer may assay delivered metal after receipt and report a different accepted fine-metal quantity. The future design must link each customer assay/certificate to the original customer, delivery, individual bar(s), approved post-casting bar assays, originating output lot(s), refining round lineage and original Sales Invoice or tolling settlement. Allow successive customer assays, disputed results, documented approval/supersession and one authoritative accepted commercial result; preserve the original measured/certified results without overwriting them.

Required outcomes to design and test after refining stabilization:

1. **Customer accepted quantity below delivered/billed fine metal:** calculate the shortfall by metal and UOM with contract-defined pricing/tolerance; issue an authorized credit note against the original invoice where commercially applicable. Track rejected fine-metal quantity pending a separately approved write-off. Do **not** auto-return or write off physical stock merely because the customer reported an assay difference.
2. **Customer accepted quantity above delivered/billed fine metal:** calculate the surplus and appropriate supplementary billing/debit adjustment. Reverse only previously *posted and eligible* losses/write-offs up to their unreversed amounts; otherwise classify and approve any gain independently. Never manufacture inventory through a commercial assay difference.
3. **Re-assay/arbitration:** compare the latest approved commercial result against cumulative prior settlements; create only the **net incremental** credit/debit/reversal, avoiding duplicate adjustments across rounds.
4. **Ownership and posting:** distinguish refinery-owned sales from customer-owned/toll-refined metal. Apply stock movements only with verified physical ownership and custody events; make ERPNext transactions company-scoped, permission-gated, idempotent and cancellation/reversal safe. Identify tax, valuation, revenue and inventory-ledger treatment explicitly before implementation.
5. **Controls and reporting:** preserve per-metal physical weight, purity, fine weight, original release figures, customer-accepted figures, variance, supporting certificates and signed approvals. Expose pending disputes, credit notes, unreconciled quantities, pending write-offs and reversals through permission-safe navigation, Number Cards, Charts and Dashboard after the dependent feature is approved.

**Dependency review gate:** After multi-round refining and mandatory post-casting bar QC are implemented and verified, assess reuse of Metal Assay stage/supersession, per-metal mass balance, bar-to-output-to-round lineage, ownership and ERPNext posting bridge. Define settlement quantity versus physical inventory quantity, then approve and implement the downstream feature separately. Its absence does not waive any mandatory bar-QC or release gate in PR #10.

## Positive tests

- Gold input produces recovered silver and palladium outputs only when the input assay has corresponding Ag and Pd components.
- Round 1 output lot becomes Round 2 input; Round 2 output lot becomes Round 3 input; lineage and round numbers remain correct.
- A second submitted assay supersedes an earlier submitted assay for the same lot and sample; the newest input purity is enforced.
- A final assay measurement differing from provisional output purity governs finished-metal reconciliation and bar capacity.
- Two batches consume nonoverlapping portions of one output lot; total allocation stays within available gross weight.
- Under the same batch, refining operating cost invoices remain linked to their specific batch.
- Existing historical batches receive round 1 and unchanged intake provenance.
- Workspace number card and chart reflect submitted batches with round number greater than 1.
- Source and target customer ownership, company and UOM remain identical.

## Negative tests

- Reject re-refining source output without a submitted lot assay, using an outdated assay, or selecting an assay of the wrong lot/company.
- Reject source output consumption exceeding the lot's available gross weight, including concurrent submissions.
- Reject recovered Pd/Ag fine metal exceeding the input assay's independently measured Pd/Ag content.
- Reject source cancellation while downstream batches or submitted output assays exist.
- Reject bar registration before the final assay and batch reconciliation or if that output has been passed to another round.
- Reject final reconciliation when any finished output lacks the latest Final assay, or its final assay creates more fine metal than available inputs.
- Reject cross-company, cross-owner, mixed-primary-metal and mixed-UOM batch inputs.
- Reject a supersession chain that references another lot/sample or contains cycles.

## Verification commands

```bash
bench --site YOUR_SITE migrate
bench --site YOUR_SITE clear-cache
bench --site YOUR_SITE run-tests --app metal_refinery_tz --module metal_refinery_tz.tests.test_refining_rounds
```

Verify imported `Refining Batch`, `Metal Lot`, `Metal Assay`, `Repeat Refining Rounds` Number Card, `Refining Rounds by Number` Chart, `Metal Refinery Operations` Dashboard, Sidebar and Workspace. Test as Stock User, Stock Manager and System Manager; a standard Dashboard or a public card is not a substitute for underlying record permissions.

**Deployment limitation:** Existing posting bridge generates opt-in ERPNext draft documents only. Automatic multi-round manufacturing, byproduct inventory valuation, and posted GL/stock movement are not added by this PR.
