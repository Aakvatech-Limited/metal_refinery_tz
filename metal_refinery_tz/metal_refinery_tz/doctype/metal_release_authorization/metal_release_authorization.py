from frappe.model.document import Document
from metal_refinery_tz.metal_refinery_tz.services.tolling import (
    validate_release, submit_release, cancel_release
)


class MetalReleaseAuthorization(Document):
    def validate(self):
        validate_release(self)

    def on_submit(self):
        submit_release(self)

    def on_cancel(self):
        cancel_release(self)
