from frappe.model.document import Document
from metal_refinery_tz.metal_refinery_tz.services.custody import validate_count


class MetalCustodyCount(Document):
    def validate(self):
        validate_count(self)
