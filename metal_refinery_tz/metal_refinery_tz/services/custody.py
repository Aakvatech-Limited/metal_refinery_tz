"""Custody controls; no ERPNext Stock Entry or GL posting is performed."""
import frappe
from frappe import _

from metal_refinery_tz.metal_refinery_tz.services.metal_math import decimal, positive, nonnegative


def _warehouse_company(warehouse, company):
    if frappe.db.get_value("Warehouse", warehouse, "company") != company:
        frappe.throw(_("Warehouse must belong to {0}").format(company))


def _unprocessed(lot_name):
    references = frappe.get_all(
        "Refining Batch Input", filters={"metal_lot": lot_name},
        fields=["parent"],
    )
    for row in references:
        if frappe.db.get_value("Refining Batch", row.parent, "docstatus") == 1:
            frappe.throw(_("Lot {0} already has submitted refining allocations").format(lot_name))


def validate_transfer(doc):
    if doc.source_warehouse == doc.target_warehouse:
        frappe.throw(_("Source and destination must differ"))
    _warehouse_company(doc.source_warehouse, doc.company)
    _warehouse_company(doc.target_warehouse, doc.company)
    if not doc.items:
        frappe.throw(_("Add at least one lot"))
    if doc.released_by == doc.received_by:
        frappe.throw(_("Release and receipt must be acknowledged by different users"))
    seen = set()
    for row in doc.items:
        if row.metal_lot in seen:
            frappe.throw(_("Duplicate lot in transfer"))
        seen.add(row.metal_lot)
        lot = frappe.get_doc("Metal Lot", row.metal_lot)
        if lot.company != doc.company or lot.warehouse != doc.source_warehouse:
            frappe.throw(_("Lot company or current custody warehouse mismatch"))
        if lot.status != "Available" or lot.uom != row.uom:
            frappe.throw(_("Lot must be available and use the same UOM"))
        positive(row.weight, _("Transfer weight"))
        if abs(decimal(row.weight) - decimal(lot.initial_weight)) > decimal("0.000001"):
            frappe.throw(_("Only whole-lot transfers are supported"))
        _unprocessed(lot.name)


def submit_transfer(doc):
    validate_transfer(doc)
    for row in doc.items:
        frappe.db.set_value("Metal Lot", row.metal_lot, "warehouse", doc.target_warehouse)


def cancel_transfer(doc):
    for row in doc.items:
        if frappe.db.get_value("Metal Lot", row.metal_lot, "warehouse") != doc.target_warehouse:
            frappe.throw(_("Lot custody location has changed since transfer"))
        later = frappe.get_all("Metal Custody Transfer Item", filters={"metal_lot": row.metal_lot}, fields=["parent"])
        for item in later:
            if item.parent != doc.name and frappe.db.get_value("Metal Custody Transfer", item.parent, "docstatus") == 1:
                frappe.throw(_("Cancel subsequent transfers first"))
        _unprocessed(row.metal_lot)
    for row in doc.items:
        frappe.db.set_value("Metal Lot", row.metal_lot, "warehouse", doc.source_warehouse)


def validate_count(doc):
    _warehouse_company(doc.warehouse, doc.company)
    nonnegative(doc.tolerance, _("Count tolerance"))
    if doc.counted_by == doc.reviewed_by:
        frappe.throw(_("Count reviewer must differ from counter"))
    if not doc.items:
        frappe.throw(_("Count requires at least one lot"))
    seen = set()
    exceeds = False
    for row in doc.items:
        if row.metal_lot in seen:
            frappe.throw(_("Duplicate lot in count"))
        seen.add(row.metal_lot)
        lot = frappe.get_doc("Metal Lot", row.metal_lot)
        if lot.company != doc.company or lot.warehouse != doc.warehouse:
            frappe.throw(_("Count lot is not in the selected company and warehouse"))
        if lot.uom != row.uom or lot.status != "Available":
            frappe.throw(_("Lot UOM or availability does not match"))
        _unprocessed(lot.name)
        nonnegative(row.counted_weight, _("Counted weight"))
        row.recorded_weight = lot.initial_weight
        row.variance = float(decimal(row.counted_weight) - decimal(row.recorded_weight))
        exceeds = exceeds or abs(decimal(row.variance)) > decimal(doc.tolerance)
    if doc.docstatus == 1 and exceeds:
        if not doc.approved_exception:
            frappe.throw(_("Over-tolerance count requires an approved exception"))
        ex = frappe.get_doc("Metal Exception", doc.approved_exception)
        if (ex.docstatus != 1 or ex.company != doc.company
            or ex.reference_doctype != "Metal Custody Count"
            or ex.reference_name != doc.name):
            frappe.throw(_("Approved exception must reference this custody count"))
