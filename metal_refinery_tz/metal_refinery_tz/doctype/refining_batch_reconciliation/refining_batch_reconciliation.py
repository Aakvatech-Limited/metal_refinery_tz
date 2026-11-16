from frappe.model.document import Document
from metal_refinery_tz.metal_refinery_tz.services.refining import validate_reconciliation


class RefiningBatchReconciliation(Document):
    def validate(self):
        validate_reconciliation(self)

    def on_submit(self):
        import frappe
        from metal_refinery_tz.metal_refinery_tz.services.refining_rounds import require_final_outputs
        batch = frappe.get_doc("Refining Batch", self.refining_batch)
        if any(row.output_type == "Finished Metal" for row in batch.outputs):
            require_final_outputs(batch)
            frappe.db.set_value("Refining Batch", batch.name, "final_assay_confirmed", 1,
                                update_modified=False)
        frappe.db.set_value("Refining Batch", self.refining_batch, "status", "Closed", update_modified=False)

    def on_cancel(self):
        import frappe
        frappe.db.set_value("Refining Batch", self.refining_batch, "final_assay_confirmed", 0,
                            update_modified=False)
        frappe.db.set_value("Refining Batch", self.refining_batch, "status", "Awaiting Reconciliation", update_modified=False)
