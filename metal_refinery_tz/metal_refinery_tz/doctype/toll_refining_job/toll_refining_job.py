import frappe
from frappe import _
from frappe.model.document import Document

from metal_refinery_tz.metal_refinery_tz.services.tolling import validate_job
from metal_refinery_tz.metal_refinery_tz.services.posting_bridge import (
    create_toll_sales_invoice_draft,
    block_cancel_if_linked,
)


class TollRefiningJob(Document):
    def validate(self):
        validate_job(self)

    def on_submit(self):
        create_toll_sales_invoice_draft(self)

    def on_cancel(self):
        if frappe.db.exists("Metal Release Authorization", {
            "toll_refining_job": self.name, "docstatus": 1
        }):
            frappe.throw(_("Cancel the linked release authorization first"))
        block_cancel_if_linked("Sales Invoice", [self.sales_invoice])
