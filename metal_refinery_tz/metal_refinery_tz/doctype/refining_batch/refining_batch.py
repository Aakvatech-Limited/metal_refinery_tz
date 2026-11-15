from frappe.model.document import Document
from metal_refinery_tz.metal_refinery_tz.services.refining import calculate_batch


class RefiningBatch(Document):
    def validate(self):
        calculate_batch(self)
        self.status = "Awaiting Reconciliation" if self.docstatus == 1 else "Draft"

    def on_cancel(self):
        import frappe
        from frappe import _
        if frappe.db.exists("Metal Bar Register", {"refining_batch": self.name}):
            frappe.throw(_("Cannot cancel a batch with registered bars"))
        if frappe.db.exists("Toll Refining Job", {"refining_batch": self.name}):
            frappe.throw(_("Cannot cancel a batch referenced by toll refining jobs"))
        if frappe.db.exists("Refining Batch Reconciliation", {"refining_batch": self.name, "docstatus": 1}):
            frappe.throw(_("Cancel the reconciliation before cancelling the batch"))
