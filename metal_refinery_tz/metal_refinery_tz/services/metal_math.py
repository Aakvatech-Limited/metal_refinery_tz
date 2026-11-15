"""Decimal-based metal arithmetic: calculations use one consistent weight UOM."""
from decimal import Decimal, ROUND_HALF_UP

import frappe
from frappe import _


def decimal(value):
    return Decimal(str(value or 0))


def weight(value):
    """Use six decimal places for fine weight; never round intermediate steps."""
    return decimal(value).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def positive(value, label):
    if decimal(value) <= 0:
        frappe.throw(_("{0} must be greater than zero").format(label))


def nonnegative(value, label):
    if decimal(value) < 0:
        frappe.throw(_("{0} cannot be negative").format(label))


def purity(value):
    value = decimal(value)
    if value < 0 or value > 100:
        frappe.throw(_("Purity must be between 0 and 100 percent"))
    return value


def fine(gross, percent):
    positive(gross, _("Metal weight"))
    return weight(decimal(gross) * purity(percent) / Decimal(100))


def same_company(doc, referenced_doctype, name):
    if not name:
        return
    company = frappe.db.get_value(referenced_doctype, name, "company")
    if not company or company != doc.company:
        frappe.throw(_("{0} {1} must belong to company {2}").format(referenced_doctype, name, doc.company))


def submitted(doctype, name):
    if frappe.db.get_value(doctype, name, "docstatus") != 1:
        frappe.throw(_("{0} {1} must be submitted").format(doctype, name))
