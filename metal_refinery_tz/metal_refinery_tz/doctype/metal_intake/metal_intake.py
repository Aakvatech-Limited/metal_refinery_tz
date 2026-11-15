from frappe.model.document import Document
from metal_refinery_tz.metal_refinery_tz.services.intake import validate_intake, create_lot, cancel_lot


class MetalIntake(Document):
    def validate(self):
        validate_intake(self)

    def on_submit(self):
        create_lot(self)

    def on_cancel(self):
        cancel_lot(self)
