"""Validate third-party metal ownership, contractual fees and documented release."""
import frappe
from frappe import _
from frappe.utils import getdate

from metal_refinery_tz.metal_refinery_tz.services.metal_math import decimal, positive, nonnegative


def validate_agreement(doc):
    if getdate(doc.valid_to) < getdate(doc.valid_from):
        frappe.throw(_("Agreement end date precedes start date"))
    if not doc.rates:
        frappe.throw(_("At least one toll refining rate is required"))
    seen = set()
    for row in doc.rates:
        if row.metal_type in seen:
            frappe.throw(_("Duplicate metal type in toll rates"))
        seen.add(row.metal_type)
        positive(row.rate_per_weight_unit, _("Service rate"))
        nonnegative(row.minimum_fee, _("Minimum fee"))


def validate_job(doc):
    agreement = frappe.get_doc("Toll Refining Agreement", doc.agreement)
    intake = frappe.get_doc("Metal Intake", doc.metal_intake)
    batch = frappe.get_doc("Refining Batch", doc.refining_batch)
    if agreement.docstatus != 1 or intake.docstatus != 1 or batch.docstatus != 1:
        frappe.throw(_("Agreement, intake and batch must be submitted"))
    if any(d.company != doc.company for d in (agreement, intake, batch)):
        frappe.throw(_("Company must match all linked records"))
    if agreement.customer != doc.customer or intake.party != doc.customer:
        frappe.throw(_("Customer must match agreement and intake"))
    if intake.party_type != "Customer" or intake.ownership != "Customer Owned":
        frappe.throw(_("Only customer-owned metal qualifies for toll refining"))
    if batch.ownership != "Customer Owned" or batch.metal_type != doc.metal_type:
        frappe.throw(_("Refining batch ownership or metal does not match"))
    if intake.metal_type != doc.metal_type or intake.uom != doc.weight_uom:
        frappe.throw(_("Intake metal or weight UOM mismatch"))
    if batch.weight_uom != doc.weight_uom:
        frappe.throw(_("Batch weight UOM mismatch"))
    if not (getdate(agreement.valid_from) <= getdate(intake.posting_date) <= getdate(agreement.valid_to)):
        frappe.throw(_("Intake is outside the agreement validity period"))
    lot = frappe.db.get_value("Metal Lot", {"intake": intake.name}, "name")
    if not lot:
        frappe.throw(_("Customer Metal Lot is missing"))
    lot_names = [r.metal_lot for r in batch.inputs]
    if lot not in lot_names:
        frappe.throw(_("Refining batch must include this customer's intake lot"))
    # Never combine different customers' metal under a single toll job.
    for lot_name in lot_names:
        input_lot = frappe.get_doc("Metal Lot", lot_name)
        if input_lot.owner_party != doc.customer or input_lot.ownership != "Customer Owned":
            frappe.throw(_("Toll batch includes another customer's metal"))
    rates = [r for r in agreement.rates if r.metal_type == doc.metal_type and r.weight_uom == doc.weight_uom]
    if len(rates) != 1:
        frappe.throw(_("Exactly one matching toll rate is required"))
    rate = rates[0]
    doc.metal_lot = lot
    doc.received_weight = intake.net_weight
    doc.rate_per_unit = rate.rate_per_weight_unit
    doc.service_fee = float(max(
        decimal(doc.received_weight) * decimal(doc.rate_per_unit),
        decimal(rate.minimum_fee)
    ))
    doc.currency = agreement.currency
    if doc.sales_invoice:
        si = frappe.get_doc("Sales Invoice", doc.sales_invoice)
        if si.company != doc.company or si.customer != doc.customer:
            frappe.throw(_("Sales Invoice company or customer differs from the toll job"))


def validate_release(doc):
    job = frappe.get_doc("Toll Refining Job", doc.toll_refining_job)
    if job.docstatus != 1 or job.company != doc.company or job.customer != doc.customer:
        frappe.throw(_("Release requires a matching submitted toll job"))
    if len({doc.authorized_by, doc.released_by, doc.received_by}) != 3:
        frappe.throw(_("Authorization, handover and receipt require separate users"))
    if doc.docstatus == 1 and doc.authorized_by != frappe.session.user:
        frappe.throw(_("Only the named authorized user may submit the release"))
    if not doc.bars:
        frappe.throw(_("Specify at least one registered bar"))
    seen = set()
    for row in doc.bars:
        if row.bar in seen:
            frappe.throw(_("Duplicate bar in release"))
        seen.add(row.bar)
        bar = frappe.get_doc("Metal Bar Register", row.bar)
        if (bar.company != doc.company or bar.refining_batch != job.refining_batch
            or bar.owner_customer != doc.customer or bar.ownership != "Customer Owned"):
            frappe.throw(_("Bar custody/ownership does not match the toll job"))
        if bar.status != "In Vault" and doc.docstatus == 1:
            frappe.throw(_("Only in-vault bars may be released"))
        row.gross_weight = bar.weight
        row.fine_weight = bar.fine_weight
        row.uom = bar.uom


def submit_release(doc):
    for row in doc.bars:
        frappe.db.set_value("Metal Bar Register", row.bar, "status", "Released")


def cancel_release(doc):
    if frappe.db.exists("Metal Export Shipment", {
        "release_authorization": doc.name, "docstatus": 1
    }):
        frappe.throw(_("Cancel the export shipment before reversing release"))
    for row in doc.bars:
        frappe.db.set_value("Metal Bar Register", row.bar, "status", "In Vault")
