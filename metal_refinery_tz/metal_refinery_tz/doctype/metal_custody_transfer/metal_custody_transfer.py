from frappe.model.document import Document
from metal_refinery_tz.metal_refinery_tz.services.custody import (
    validate_transfer, submit_transfer, cancel_transfer
)


class MetalCustodyTransfer(Document):
    def validate(self):
        validate_transfer(self)

    def on_submit(self):
        submit_transfer(self)

    def on_cancel(self):
        cancel_transfer(self)
