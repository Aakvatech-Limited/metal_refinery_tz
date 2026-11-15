import frappe
from frappe import _
from frappe.model.document import Document

from metal_refinery_tz.metal_refinery_tz.services.refining import calculate_batch
from metal_refinery_tz.metal_refinery_tz.services.posting_bridge import (
    validate_operating_costs,
    create_operating_cost_invoices,
    create_wip_transfer_draft,
    block_cancel_if_linked,
)


class RefiningBatch(Document):
    def validate(self):
        calculate_batch(self)
        validate_operating_costs(self)
        self.status = "Awaiting Reconciliation" if self.docstatus == 1 else "Draft"

    def on_submit(self):
        create_operating_cost_invoices(self)
        create_wip_transfer_draft(self)

    def on_cancel(self):
        if frappe.db.exists("Metal Bar Register", {"refining_batch": self.name}):
            frappe.throw(_("Cannot cancel a batch with registered bars"))
        if frappe.db.exists("Toll Refining Job", {"refining_batch": self.name}):
            frappe.throw(_("Cannot cancel a batch referenced by toll refining jobs"))
        if frappe.db.exists("Refining Batch Reconciliation", {"refining_batch": self.name, "docstatus": 1}):
            frappe.throw(_("Cancel the reconciliation before cancelling the batch"))
        block_cancel_if_linked("Stock Entry", [self.stock_entry])
        for row in self.get("operating_costs") or []:
            block_cancel_if_linked("Purchase Invoice", [row.purchase_invoice])
