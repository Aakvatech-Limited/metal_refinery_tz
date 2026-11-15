from frappe import _
import frappe
from frappe.model.document import Document
from metal_refinery_tz.metal_refinery_tz.services.metal_math import positive


class MetalPriceFixing(Document):
    def validate(self):
        positive(self.rate_per_fine_unit, _("Price per fine unit"))
        if not self.reference_source:
            frappe.throw(_("A pricing reference is required"))
