from frappe.model.document import Document
from metal_refinery_tz.metal_refinery_tz.services.tolling import validate_job


class TollRefiningJob(Document):
    def validate(self):
        validate_job(self)

    def on_cancel(self):
        import frappe
        from frappe import _
        if frappe.db.exists("Metal Release Authorization", {
            "toll_refining_job": self.name, "docstatus": 1
        }):
            frappe.throw(_("Cancel the linked release authorization first"))
