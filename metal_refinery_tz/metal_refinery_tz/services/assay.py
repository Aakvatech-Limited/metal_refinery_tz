"""Assay and sample validation for intake and intermediate refined lots."""
import frappe
from frappe import _

from metal_refinery_tz.metal_refinery_tz.services.metal_math import (
    decimal, fine, positive, same_company, submitted,
)


def validate_assay(doc):
    if bool(doc.metal_intake) == bool(doc.metal_lot):
        frappe.throw(_("Select either Metal Intake or an intermediate Metal Lot"))
    positive(doc.sample_weight, _("Sample weight"))
    if doc.metal_lot:
        same_company(doc, "Metal Lot", doc.metal_lot)
        lot = frappe.get_doc("Metal Lot", doc.metal_lot)
        if not lot.source_refining_batch:
            frappe.throw(_("Intermediate assay must reference a refinery output lot"))
        submitted("Refining Batch", lot.source_refining_batch)
        if doc.uom != lot.uom or decimal(doc.sample_weight) > decimal(lot.initial_weight):
            frappe.throw(_("Sample weight/UOM exceeds the originating metal lot"))
    else:
        same_company(doc, "Metal Intake", doc.metal_intake)
        submitted("Metal Intake", doc.metal_intake)
        intake = frappe.get_doc("Metal Intake", doc.metal_intake)
        samples = {row.sample_id: row for row in intake.samples}
        if doc.sample_id not in samples:
            frappe.throw(_("Sample ID must be recorded in selected intake"))
        if doc.uom != samples[doc.sample_id].uom:
            frappe.throw(_("Assay sample and intake sample must use the same UOM"))
        if decimal(doc.sample_weight) > decimal(samples[doc.sample_id].sample_weight):
            frappe.throw(_("Assay sample weight exceeds recorded sample weight"))
    if not doc.results:
        frappe.throw(_("At least one assay result is required"))
    used = set()
    total = decimal(0)
    for result in doc.results:
        if result.metal_type in used:
            frappe.throw(_("Duplicate metal in assay results"))
        used.add(result.metal_type)
        total += decimal(result.purity_percent)
        result.fine_metal_weight = float(fine(doc.sample_weight, result.purity_percent))
    if total > 100:
        frappe.throw(_("Combined assay percentages cannot exceed 100"))
    if doc.supersedes:
        if doc.supersedes == doc.name:
            frappe.throw(_("An assay cannot supersede itself"))
        previous = frappe.get_doc("Metal Assay", doc.supersedes)
        if (previous.metal_intake != doc.metal_intake
                or previous.metal_lot != doc.metal_lot
                or previous.sample_id != doc.sample_id):
            frappe.throw(_("Superseded assay must reference the same material and sample"))
        submitted("Metal Assay", previous.name)
        visited = {doc.name}
        cursor = previous
        while cursor:
            if cursor.name in visited:
                frappe.throw(_("Assay supersession cycle detected"))
            visited.add(cursor.name)
            cursor = frappe.get_doc("Metal Assay", cursor.supersedes) if cursor.supersedes else None


def require_final_assay(intake_name, assay_name, metal_type):
    assay = frappe.get_doc("Metal Assay", assay_name)
    if assay.metal_intake != intake_name or assay.assay_status != "Final":
        frappe.throw(_("Settlement requires a final assay for this intake"))
    submitted("Metal Assay", assay_name)
    if frappe.db.exists("Metal Assay", {
        "supersedes": assay_name, "docstatus": 1, "assay_status": "Final"
    }):
        frappe.throw(_("A newer approved assay supersedes the selected result"))
    matched = [row for row in assay.results if row.metal_type == metal_type]
    if len(matched) != 1:
        frappe.throw(_("Assay must contain one result for the purchased metal"))
    return matched[0]
