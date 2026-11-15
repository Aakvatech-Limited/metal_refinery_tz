from frappe.model.document import Document

from metal_refinery_tz.metal_refinery_tz.services.settlement import calculate_settlement
from metal_refinery_tz.metal_refinery_tz.services.posting_bridge import (
    create_purchase_receipt_draft,
    block_cancel_if_linked,
)


class MetalPurchaseSettlement(Document):
    def validate(self):
        calculate_settlement(self)

    def on_submit(self):
        create_purchase_receipt_draft(self)

    def on_cancel(self):
        block_cancel_if_linked("Purchase Receipt", [self.purchase_receipt])
        block_cancel_if_linked("Purchase Invoice", [self.purchase_invoice])
