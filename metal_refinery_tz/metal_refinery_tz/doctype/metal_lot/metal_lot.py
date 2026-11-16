import frappe
from frappe import _
from frappe.model.document import Document


class MetalLot(Document):
    """A traceable custody record created by submitting a Metal Intake."""

    def validate(self):
        if bool(self.intake) == bool(self.source_refining_batch):
            frappe.throw(_("Lot must originate from exactly one intake or refining batch"))
        if self.source_refining_batch:
            batch = frappe.get_doc("Refining Batch", self.source_refining_batch)
            if batch.docstatus != 1:
                frappe.throw(_("Source batch must be submitted"))
            outputs = [r for r in batch.outputs if r.name == self.source_output_row]
            if len(outputs) != 1:
                frappe.throw(_("Source output row does not belong to this batch"))
            output = outputs[0]
            expected = {"company": batch.company, "metal_type": output.metal_type,
                        "ownership": batch.ownership, "uom": output.uom}
            for field, value in expected.items():
                if self.get(field) != value:
                    frappe.throw(_("Output lot {0} differs from source").format(field))
            if abs(float(self.initial_weight) - float(output.weight)) > 0.000001:
                frappe.throw(_("Output lot weight must equal source output weight"))
            old = self.get_doc_before_save()
            if old:
                for field in (*expected, "initial_weight", "intake", "source_refining_batch",
                              "source_output_row", "owner_party", "owner_party_type"):
                    if self.get(field) != old.get(field):
                        frappe.throw(_("Output lot provenance cannot be amended"))
            return
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
            for field in (*expected.keys(), "initial_weight", "intake", "source_refining_batch", "source_output_row"):
                if self.get(field) != existing.get(field):
                    frappe.throw(_("Lot provenance and ownership fields cannot be amended"))
