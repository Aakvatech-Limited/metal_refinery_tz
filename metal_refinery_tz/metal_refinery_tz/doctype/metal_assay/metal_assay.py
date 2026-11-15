from frappe.model.document import Document
from metal_refinery_tz.metal_refinery_tz.services.assay import validate_assay


class MetalAssay(Document):
    def validate(self):
        validate_assay(self)
