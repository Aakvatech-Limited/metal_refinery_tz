from frappe.model.document import Document
from metal_refinery_tz.metal_refinery_tz.services.operations import validate_operation


class RefiningOperation(Document):
    def validate(self):
        validate_operation(self)
