from frappe.model.document import Document
from metal_refinery_tz.metal_refinery_tz.services.bullion import validate_bar


class MetalBarRegister(Document):
    def validate(self):
        validate_bar(self)
