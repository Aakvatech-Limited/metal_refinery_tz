"""Purchase settlement: price fixing, approved assay, deductions; no auto invoices."""
import frappe
from frappe import _

from metal_refinery_tz.metal_refinery_tz.services.assay import require_final_assay
from metal_refinery_tz.metal_refinery_tz.services.metal_math import (
    decimal, weight, positive, same_company, submitted,
)


def calculate_settlement(doc):
    intake = frappe.get_doc("Metal Intake", doc.metal_intake)
    same_company(doc, "Metal Intake", intake.name)
    submitted("Metal Intake", intake.name)
    if intake.party_type != "Supplier" or intake.ownership != "Company Owned":
        frappe.throw(_("Purchase settlement is only allowed for company-owned supplier intakes"))
    if doc.metal_type != intake.metal_type:
        frappe.throw(_("Settlement metal must match intake metal"))
    result = require_final_assay(intake.name, doc.assay, doc.metal_type)
    price = frappe.get_doc("Metal Price Fixing", doc.price_fixing)
    submitted("Metal Price Fixing", price.name)
    same_company(doc, "Metal Price Fixing", price.name)
    if price.metal_type != doc.metal_type or price.currency != doc.currency:
        frappe.throw(_("Price fixing metal and currency must match settlement"))
    if intake.uom != price.weight_uom:
        frappe.throw(_("Price fixing weight UOM must match intake UOM"))
    if frappe.get_doc("Metal Assay", doc.assay).uom != intake.uom:
        frappe.throw(_("Assay and intake must use the same UOM"))
    positive(price.rate_per_fine_unit, _("Price fixing rate"))
    if not doc.assay:
        frappe.throw(_("Assay is required"))

    # Apply representative sample purity to the full intake, NOT sample weight.
    gross_fine = weight(decimal(intake.net_weight) * decimal(result.purity_percent) / 100)
    positive(gross_fine, _("Fine metal weight"))
    rate = decimal(price.rate_per_fine_unit)
    gross = gross_fine * rate
    deduction = sum((decimal(x.amount) for x in (doc.charges or [])), decimal(0))
    net = gross - deduction
    if net < 0:
        frappe.throw(_("Net settlement cannot be negative"))
    doc.fine_weight = float(gross_fine)
    doc.rate_per_fine_unit = float(rate)
    doc.gross_amount = float(gross)
    doc.total_deductions = float(deduction)
    doc.net_amount = float(net)
    if doc.purchase_invoice:
        invoice = frappe.get_doc("Purchase Invoice", doc.purchase_invoice)
        if invoice.company != doc.company or invoice.supplier != intake.party:
            frappe.throw(_("Linked Purchase Invoice must match company and supplier"))
