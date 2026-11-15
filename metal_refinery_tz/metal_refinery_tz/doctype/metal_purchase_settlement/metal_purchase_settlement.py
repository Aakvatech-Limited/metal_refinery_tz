from frappe.model.document import Document
from metal_refinery_tz.metal_refinery_tz.services.settlement import calculate_settlement


class MetalPurchaseSettlement(Document):
    def validate(self):
        calculate_settlement(self)
