from frappe.model.document import Document


class MetalERPNextPostingProfile(Document):
    def validate(self):
        from metal_refinery_tz.metal_refinery_tz.services.posting_bridge import validate_profile
        validate_profile(self)
