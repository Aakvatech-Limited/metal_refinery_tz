from frappe.model.document import Document
from metal_refinery_tz.metal_refinery_tz.services.tolling import validate_agreement


class TollRefiningAgreement(Document):
    def validate(self):
        validate_agreement(self)
