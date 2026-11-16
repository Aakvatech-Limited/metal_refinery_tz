"""Batch metal balance and ownership validation without automatic stock postings."""
from collections import defaultdict
from decimal import Decimal

import frappe
from frappe import _

from metal_refinery_tz.metal_refinery_tz.services.metal_math import (
    decimal, fine, positive, weight, same_company, submitted,
)


def calculate_batch(doc):
    if not doc.inputs:
        frappe.throw(_("Refining batch requires at least one input lot"))
    input_totals = defaultdict(lambda: Decimal(0))
    output_totals = defaultdict(lambda: Decimal(0))
    seen = set()
    for row in doc.inputs:
        if row.metal_lot in seen:
            frappe.throw(_("A metal lot must occur only once per refining batch"))
        seen.add(row.metal_lot)
        lot = frappe.get_doc("Metal Lot", row.metal_lot)
        if lot.company != doc.company or lot.metal_type != row.metal_type:
            frappe.throw(_("Input lot company or metal does not match"))
        if lot.metal_type != doc.metal_type or lot.ownership != doc.ownership:
            frappe.throw(_("Mixed ownership or mixed metals are not supported in this release"))
        if lot.uom != doc.weight_uom or row.uom != doc.weight_uom:
            frappe.throw(_("All input weights must use the batch UOM"))
        positive(row.input_weight, _("Input weight"))
        if decimal(row.input_weight) > decimal(lot.initial_weight):
            frappe.throw(_("Input weight exceeds lot initial weight"))
        row.fine_weight = float(fine(row.input_weight, row.purity_percent))
        input_totals[row.metal_type] += decimal(row.fine_weight)
    for row in doc.outputs or []:
        if row.uom != doc.weight_uom:
            frappe.throw(_("Output weight UOM must match the batch"))
        row.fine_weight = float(fine(row.weight, row.purity_percent))
        if row.metal_type == doc.metal_type:
            output_totals[row.metal_type] += decimal(row.fine_weight)
    doc.input_fine_weight = float(weight(sum(input_totals.values(), Decimal(0))))
    doc.output_fine_weight = float(weight(sum(output_totals.values(), Decimal(0))))
    doc.unaccounted_fine_weight = float(weight(decimal(doc.input_fine_weight) - decimal(doc.output_fine_weight)))
    if doc.docstatus == 1 and not doc.outputs:
        frappe.throw(_("A submitted refining batch requires recorded output, loss or WIP rows"))
    # Inputs can be allocated across batches, but never beyond available source lot weight.
    if doc.docstatus == 1:
        for row in doc.inputs:
            historical = frappe.get_all(
                "Refining Batch Input", filters={"metal_lot": row.metal_lot},
                fields=["parent", "input_weight"],
            )
            allocated = decimal(row.input_weight)
            checked = set()
            for old in historical:
                if old.parent == doc.name:
                    continue
                if old.parent in checked:
                    continue
                checked.add(old.parent)
                if frappe.db.get_value("Refining Batch", old.parent, "docstatus") == 1:
                    allocated += decimal(old.input_weight)
            lot_weight = decimal(frappe.db.get_value("Metal Lot", row.metal_lot, "initial_weight"))
            if allocated > lot_weight:
                frappe.throw(_("Submitted batch allocations exceed initial lot weight: {0}").format(row.metal_lot))


def validate_reconciliation(doc):
    batch = frappe.get_doc("Refining Batch", doc.refining_batch)
    submitted("Refining Batch", batch.name)
    same_company(doc, "Refining Batch", batch.name)
    if batch.metal_type != doc.metal_type:
        frappe.throw(_("Reconciliation metal differs from batch metal"))
    doc.input_fine_weight = batch.input_fine_weight
    doc.accounted_fine_weight = batch.output_fine_weight
    doc.variance_fine_weight = batch.unaccounted_fine_weight
    variance = abs(decimal(doc.variance_fine_weight))
    tolerance = decimal(doc.tolerance)
    if tolerance < 0:
        frappe.throw(_("Tolerance cannot be negative"))
    if variance > tolerance:
        if not doc.variance_reason or not doc.approved_exception:
            frappe.throw(_("Variance above tolerance requires a reason and approved exception"))
        exception = frappe.get_doc("Metal Exception", doc.approved_exception)
        submitted("Metal Exception", exception.name)
        if (exception.company != doc.company or
            exception.reference_doctype != "Refining Batch" or
            exception.reference_name != batch.name):
            frappe.throw(_("Approved exception must reference this refining batch"))
