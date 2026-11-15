from frappe.model.document import Document
from metal_refinery_tz.metal_refinery_tz.services.refining import validate_reconciliation


class RefiningBatchReconciliation(Document):
    def validate(self):
        validate_reconciliation(self)

    def on_submit(self):
        import frappe
        frappe.db.set_value("Refining Batch", self.refining_batch, "status", "Closed", update_modified=False)

    def on_cancel(self):
        import frappe
        frappe.db.set_value("Refining Batch", self.refining_batch, "status", "Awaiting Reconciliation", update_modified=False)
