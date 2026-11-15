"""Assay and sample checks."""
import frappe
from frappe import _

from metal_refinery_tz.metal_refinery_tz.services.metal_math import (
    decimal, fine, positive, same_company, submitted,
)


def validate_assay(doc):
    same_company(doc, "Metal Intake", doc.metal_intake)
    submitted("Metal Intake", doc.metal_intake)
    intake = frappe.get_doc("Metal Intake", doc.metal_intake)
    samples = {row.sample_id: row for row in intake.samples}
    if doc.sample_id not in samples:
        frappe.throw(_("Sample ID must be recorded in the selected intake"))
    if doc.uom != samples[doc.sample_id].uom:
        frappe.throw(_("Assay sample and intake sample must use the same UOM"))
    positive(doc.sample_weight, _("Sample weight"))
    if decimal(doc.sample_weight) > decimal(samples[doc.sample_id].sample_weight):
        frappe.throw(_("Assay sample weight exceeds the recorded sample weight"))
    if not doc.results:
        frappe.throw(_("At least one assay result is required"))
    used = set()
    total_purity = decimal(0)
    for result in doc.results:
        if result.metal_type in used:
            frappe.throw(_("Duplicate metal in assay results"))
        used.add(result.metal_type)
        total_purity += decimal(result.purity_percent)
        result.fine_metal_weight = float(fine(doc.sample_weight, result.purity_percent))
    if total_purity > 100:
        frappe.throw(_("Combined assay percentages cannot exceed 100"))
    if doc.supersedes:
        if doc.supersedes == doc.name:
            frappe.throw(_("An assay cannot supersede itself"))
        previous = frappe.get_doc("Metal Assay", doc.supersedes)
        if previous.metal_intake != doc.metal_intake or previous.sample_id != doc.sample_id:
            frappe.throw(_("Superseded assay must reference the same intake and sample"))
        submitted("Metal Assay", previous.name)


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
