from frappe.model.document import Document
from metal_refinery_tz.metal_refinery_tz.services.bullion import validate_export


class MetalExportShipment(Document):
    def validate(self):
        validate_export(self)
