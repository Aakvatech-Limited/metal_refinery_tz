import frappe
from frappe import _
from frappe.model.document import Document


class MetalLot(Document):
    """A traceable custody record created by submitting a Metal Intake."""

    def validate(self):
        intake = frappe.get_doc("Metal Intake", self.intake)
        if intake.docstatus != 1:
            frappe.throw(_("A lot requires a submitted Metal Intake"))
        expected = {
            "company": intake.company,
            "metal_type": intake.metal_type,
            "ownership": intake.ownership,
            "owner_party": intake.party,
            "owner_party_type": intake.party_type,
            "uom": intake.uom,
        }
        for field, value in expected.items():
            if self.get(field) != value:
                frappe.throw(_("Metal lot {0} must match its intake").format(field))
        if abs(float(self.initial_weight) - float(intake.net_weight)) > 0.000001:
            frappe.throw(_("Metal lot weight must equal intake net weight"))
        existing = self.get_doc_before_save()
        if existing:
            for field in (*expected.keys(), "initial_weight", "intake"):
                if self.get(field) != existing.get(field):
                    frappe.throw(_("Lot provenance and ownership fields cannot be amended"))
