"""Provenance-preserving refining rounds and output lot lifecycle.

Intermediate output lots represent physical material, not ERPNext stock receipts.
"""
from collections import defaultdict
from decimal import Decimal

import frappe
from frappe import _
from frappe.utils import getdate

from metal_refinery_tz.metal_refinery_tz.services.metal_math import decimal, fine, weight


def latest_assay(lot_name, final_only=False):
    filters = {"metal_lot": lot_name, "docstatus": 1}
    if final_only:
        filters["assay_status"] = "Final"
    rows = frappe.get_all(
        "Metal Assay", filters=filters,
        fields=["name", "assay_status"], order_by="creation desc",
    )
    if not rows:
        return None
    latest = rows[0]
    if final_only:
        any_latest = latest_assay(lot_name)
        if not any_latest or any_latest.name != latest.name:
            return None
    return frappe.get_doc("Metal Assay", latest.name)


def assert_input_assay(row, lot):
    if not lot.source_refining_batch:
        if row.input_assay:
            assay = frappe.get_doc("Metal Assay", row.input_assay)
            if assay.docstatus != 1 or assay.company != lot.company or assay.metal_intake != lot.intake:
                frappe.throw(_("Input assay must be a submitted assay for the original intake"))
            result = next((r for r in assay.results if r.metal_type == row.metal_type), None)
            if not result or abs(decimal(result.purity_percent) - decimal(row.purity_percent)) > Decimal("0.000001"):
                frappe.throw(_("Original lot input purity must match its selected assay"))
        return
    if not row.input_assay:
        frappe.throw(_("Refined input lot {0} requires a submitted assay").format(lot.name))
    latest = latest_assay(lot.name)
    if not latest or row.input_assay != latest.name:
        frappe.throw(_("Input assay for {0} must be the latest submitted assay").format(lot.name))
    if latest.company != lot.company or latest.uom != row.uom:
        frappe.throw(_("Input assay company or weight UOM differs from lot"))
    matches = [r for r in latest.results if r.metal_type == row.metal_type]
    if len(matches) != 1 or abs(decimal(matches[0].purity_percent) - decimal(row.purity_percent)) > Decimal("0.000001"):
        frappe.throw(_("Input purity must equal latest assay result for {0}").format(row.metal_type))


def validate_round(doc):
    sources = set()
    for row in doc.inputs:
        lot = frappe.get_doc("Metal Lot", row.metal_lot)
        assert_input_assay(row, lot)
        if lot.source_refining_batch:
            sources.add(lot.source_refining_batch)
            previous = frappe.get_doc("Refining Batch", lot.source_refining_batch)
            if previous.docstatus != 1 or previous.company != doc.company:
                frappe.throw(_("Refined input must originate from submitted batch in the same company"))
            if previous.name == doc.name:
                frappe.throw(_("A refining batch cannot consume its own output"))
            # Form and API saves pass the date as a string; stored values are dates.
            if getdate(previous.batch_date) > getdate(doc.batch_date):
                frappe.throw(_("Refining round cannot predate its source batch"))
    doc.round_number = 1 + max(
        (int(frappe.db.get_value("Refining Batch", source, "round_number") or 1) for source in sources),
        default=0,
    )
    if doc.docstatus == 0:
        doc.final_assay_confirmed = 0
    # The primary metal may be separated from an alloy but must not be invented.
    input_primary = sum(
        (decimal(row.fine_weight) for row in doc.inputs if row.metal_type == doc.metal_type),
        Decimal(0),
    )
    output_primary = sum(
        (decimal(row.fine_weight) for row in doc.outputs or []
         if row.metal_type == doc.metal_type and row.output_type != "Process Loss"),
        Decimal(0),
    )
    if output_primary > input_primary + Decimal("0.000001"):
        frappe.throw(_("Recovered primary fine metal cannot exceed assayed input fine metal"))
    # Each recovered byproduct must be supported by actual input assay composition.
    other_metals = {row.metal_type for row in doc.outputs or []
                    if row.metal_type != doc.metal_type and row.output_type != "Process Loss"}
    if other_metals:
        available = defaultdict(Decimal)
        for row in doc.inputs:
            if not row.input_assay:
                frappe.throw(_("Byproduct recovery requires input assays for every input lot"))
            assay = frappe.get_doc("Metal Assay", row.input_assay)
            for result in assay.results:
                available[result.metal_type] += fine(row.input_weight, result.purity_percent)
        for metal in other_metals:
            recovered = sum(
                (decimal(r.fine_weight) for r in doc.outputs
                 if r.metal_type == metal and r.output_type != "Process Loss"),
                Decimal(0),
            )
            if recovered > available[metal] + Decimal("0.000001"):
                frappe.throw(_("Recovered {0} exceeds the input assay composition").format(metal))
    # Final metal cannot be recorded as a finished product before a final lot assay.
    if doc.docstatus == 1 and not doc.outputs:
        frappe.throw(_("A submitted refining round requires output rows"))


def create_output_lots(doc):
    for row in doc.outputs or []:
        if row.output_type in ("Process Loss", "Sample") or decimal(row.weight) <= 0:
            continue
        if row.output_lot:
            if not frappe.db.exists("Metal Lot", row.output_lot):
                frappe.throw(_("Linked output lot no longer exists"))
            continue
        if frappe.db.exists("Metal Lot", {"source_output_row": row.name}):
            frappe.throw(_("An output lot already exists for row {0}").format(row.name))
        inputs = [frappe.get_doc("Metal Lot", r.metal_lot) for r in doc.inputs]
        first = inputs[0]
        if doc.ownership == "Customer Owned" and any(
            lot.owner_party != first.owner_party for lot in inputs
        ):
            frappe.throw(_("Customer-owned input lots must have one customer owner"))
        lot = frappe.get_doc({
            "doctype": "Metal Lot",
            "source_refining_batch": doc.name,
            "source_output_row": row.name,
            "company": doc.company,
            "metal_type": row.metal_type,
            "ownership": doc.ownership,
            "owner_party_type": first.owner_party_type if doc.ownership == "Customer Owned" else None,
            "owner_party": first.owner_party if doc.ownership == "Customer Owned" else None,
            "initial_weight": row.weight,
            "uom": row.uom,
            "warehouse": first.warehouse,
            "status": "Available",
        })
        lot.insert(ignore_permissions=True)
        row.output_lot = lot.name
        frappe.db.set_value("Refining Batch Output", row.name, "output_lot", lot.name,
                            update_modified=False)


def block_cancel_with_descendants(doc):
    for row in doc.outputs or []:
        if not row.output_lot:
            continue
        if frappe.db.exists("Refining Batch Input", {"metal_lot": row.output_lot}):
            frappe.throw(_("Cannot cancel a refining round with downstream batch references"))
        if frappe.db.exists("Metal Assay", {"metal_lot": row.output_lot, "docstatus": 1}):
            frappe.throw(_("Cannot cancel a refining round with submitted output assays"))


def delete_unused_output_lots(doc):
    for row in doc.outputs or []:
        if not row.output_lot:
            continue
        block_cancel_with_descendants(doc)
        frappe.delete_doc("Metal Lot", row.output_lot, ignore_permissions=True)
        frappe.db.set_value("Refining Batch Output", row.name, "output_lot", None,
                            update_modified=False)


def confirmed_finished_fine(batch):
    """Return measured fine weight per metal; provisional output purity is historical."""
    totals = defaultdict(Decimal)
    finished = [r for r in batch.outputs if r.output_type == "Finished Metal"]
    if not finished:
        frappe.throw(_("No finished metal output exists"))
    for row in finished:
        if not row.output_lot:
            frappe.throw(_("Finished output lot is not yet created"))
        assay = latest_assay(row.output_lot, final_only=True)
        if not assay:
            frappe.throw(_("Finished output {0} requires latest final assay").format(row.output_lot))
        result = next((r for r in assay.results if r.metal_type == row.metal_type), None)
        if not result:
            frappe.throw(_("Final output assay is missing {0}").format(row.metal_type))
        totals[row.metal_type] += fine(row.weight, result.purity_percent)
    return totals


def require_final_outputs(batch):
    """Confirm the latest assays and prohibit creation of excess fine metal."""
    totals = confirmed_finished_fine(batch)
    available = defaultdict(Decimal)
    for row in batch.inputs:
        available[row.metal_type] += decimal(row.fine_weight)
        if row.input_assay:
            assay = frappe.get_doc("Metal Assay", row.input_assay)
            for component in assay.results:
                if component.metal_type != row.metal_type:
                    available[component.metal_type] += fine(
                        row.input_weight, component.purity_percent
                    )
    accounted = defaultdict(Decimal, totals)
    # Finished metal competes with residue, samples and WIP for the same
    # element. The latest final assay cannot create metal hidden in other outputs.
    for output in batch.outputs:
        if output.output_type not in ("Finished Metal", "Process Loss"):
            accounted[output.metal_type] += decimal(output.fine_weight)
    for metal, quantity in accounted.items():
        if quantity > available[metal] + Decimal("0.000001"):
            frappe.throw(
                _("Confirmed {0} fine weight plus remaining outputs exceeds input composition").format(metal)
            )
    return totals


@frappe.whitelist()
def create_next_round(source_batch, lot_names=None):
    """Create a draft next round; actual consumption occurs only at submission."""
    import json

    frappe.has_permission("Refining Batch", ptype="create", throw=True)
    batch = frappe.get_doc("Refining Batch", source_batch)
    batch.check_permission("read")
    if batch.docstatus != 1:
        frappe.throw(_("Previous refining round must be submitted"))
    if batch.final_assay_confirmed:
        frappe.throw(_("Cancel final reconciliation before reopening a finished refining chain"))
    if frappe.db.exists("Metal Bar Register", {"refining_batch": batch.name}):
        frappe.throw(_("A batch with registered bars cannot be re-refined"))
    if isinstance(lot_names, str):
        lot_names = json.loads(lot_names)
    selected = set(lot_names or [r.output_lot for r in batch.outputs if r.output_lot])
    rows = []
    for output in batch.outputs:
        if not output.output_lot or output.output_lot not in selected:
            continue
        if output.output_type not in ("Closing WIP", "Recoverable Residue", "Finished Metal"):
            frappe.throw(_("Only physically recoverable outputs can be refined again"))
        assay = latest_assay(output.output_lot)
        if not assay:
            frappe.throw(_("Output lot {0} requires an assay before re-refining").format(output.output_lot))
        result = next((r for r in assay.results if r.metal_type == output.metal_type), None)
        if not result:
            frappe.throw(_("Assay lacks the selected metal result"))
        rows.append({
            "metal_lot": output.output_lot, "metal_type": output.metal_type,
            "ownership": batch.ownership, "input_weight": output.weight,
            "purity_percent": result.purity_percent, "uom": output.uom,
            "input_assay": assay.name,
        })
    if not rows or selected != {r["metal_lot"] for r in rows}:
        frappe.throw(_("Select valid output lots from the source batch"))
    metals = {r["metal_type"] for r in rows}
    if len(metals) != 1:
        frappe.throw(_("Select lots of the same primary metal for one refining round"))
    draft = frappe.get_doc({
        "doctype": "Refining Batch", "company": batch.company,
        "batch_date": frappe.utils.today(), "metal_type": rows[0]["metal_type"],
        "ownership": batch.ownership, "weight_uom": batch.weight_uom,
        "inputs": rows,
    })
    draft.insert()
    return draft.name
