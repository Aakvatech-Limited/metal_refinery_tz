"""Intake weighing validation and custody lot creation."""
import frappe
from frappe import _

from metal_refinery_tz.metal_refinery_tz.services.metal_math import (
    decimal, positive, nonnegative, weight,
)


def validate_intake(doc):
    if doc.ownership == "Customer Owned" and doc.party_type != "Customer":
        frappe.throw(_("Customer-owned metal intake requires a Customer"))
    if not doc.measurements:
        frappe.throw(_("At least one measurement is required"))
    finals = [r for r in doc.measurements if r.measurement_type == "Final"]
    if len(finals) != 1:
        frappe.throw(_("Exactly one final measurement is required"))
    seen = set()
    for row in doc.measurements:
        positive(row.gross_weight, _("Gross weight"))
        nonnegative(row.tare_weight, _("Tare weight"))
        net = decimal(row.gross_weight) - decimal(row.tare_weight)
        positive(net, _("Net weight"))
        row.net_weight = float(weight(net))
        if row.measurement_type in seen and row.measurement_type == "Final":
            frappe.throw(_("Only one final weight is permitted"))
        seen.add(row.measurement_type)
    final = finals[0]
    doc.net_weight = final.net_weight
    doc.uom = final.uom
    for row in doc.samples or []:
        positive(row.sample_weight, _("Sample weight"))
        if row.uom != doc.uom:
            frappe.throw(_("Sample UOM must match final measurement UOM"))
        if decimal(row.sample_weight) > decimal(doc.net_weight):
            frappe.throw(_("Sample weight exceeds intake weight"))
    if doc.warehouse:
        company = frappe.db.get_value("Warehouse", doc.warehouse, "company")
        if company != doc.company:
            frappe.throw(_("Warehouse must belong to the intake company"))


def create_lot(doc):
    if frappe.db.exists("Metal Lot", {"intake": doc.name}):
        frappe.throw(_("A Metal Lot already exists for this intake"))
    lot = frappe.get_doc({
        "doctype": "Metal Lot",
        "intake": doc.name,
        "company": doc.company,
        "metal_type": doc.metal_type,
        "ownership": doc.ownership,
        "owner_party_type": "Customer" if doc.ownership == "Customer Owned" else "Supplier",
        "owner_party": doc.party,
        "initial_weight": doc.net_weight,
        "uom": doc.uom,
        "warehouse": doc.warehouse,
        "status": "Available",
    })
    lot.insert(ignore_permissions=True)
    frappe.db.set_value("Metal Intake", doc.name, "metal_lot", lot.name, update_modified=False)


def cancel_lot(doc):
    lot = frappe.db.get_value("Metal Lot", {"intake": doc.name}, "name")
    if not lot:
        return
    if frappe.db.exists("Metal Custody Transfer Item", {"metal_lot": lot}):
        frappe.throw(_("Cannot cancel intake: lot has custody transfer history"))
    if frappe.db.exists("Toll Refining Job", {"metal_intake": doc.name}):
        frappe.throw(_("Cannot cancel intake: toll refining job references the intake"))
    if frappe.db.exists("Refining Batch Input", {"metal_lot": lot}):
        frappe.throw(_("Cannot cancel intake: lot has refining batch references"))
    if frappe.db.exists("Metal Assay", {"metal_intake": doc.name, "docstatus": 1}):
        frappe.throw(_("Cannot cancel intake: submitted assays exist"))
    if frappe.db.exists("Metal Purchase Settlement", {"metal_intake": doc.name, "docstatus": 1}):
        frappe.throw(_("Cannot cancel intake: submitted settlements exist"))
    frappe.delete_doc("Metal Lot", lot, ignore_permissions=True)
    frappe.db.set_value("Metal Intake", doc.name, "metal_lot", None, update_modified=False)
