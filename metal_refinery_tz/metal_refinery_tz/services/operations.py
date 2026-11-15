"""Operation event constraints."""
import frappe
from frappe import _
from frappe.utils import get_datetime


def validate_operation(doc):
    if doc.end_time and get_datetime(doc.end_time) < get_datetime(doc.start_time):
        frappe.throw(_("End time cannot be before start time"))
    if frappe.db.get_value("Refining Batch", doc.refining_batch, "docstatus") == 2:
        frappe.throw(_("Operations cannot be recorded against a cancelled batch"))
