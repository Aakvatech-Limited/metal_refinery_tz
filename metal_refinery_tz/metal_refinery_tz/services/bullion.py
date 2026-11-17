"""Bar identity, fine metal reconciliation, and export readiness."""
import frappe
from frappe import _

from metal_refinery_tz.metal_refinery_tz.services.metal_math import decimal, fine, positive


def validate_bar(doc):
    # Serialize bar registrations against the same parent batch so two
    # concurrent requests cannot both consume the final available balance.
    parent = frappe.qb.DocType("Refining Batch")
    frappe.qb.from_(parent).select(parent.name).where(
        parent.name == doc.refining_batch
    ).for_update().run()
    batch = frappe.get_doc("Refining Batch", doc.refining_batch)
    if batch.docstatus != 1 or batch.company != doc.company:
        frappe.throw(_("Bar requires a submitted batch in the same company"))
    if batch.ownership != doc.ownership:
        frappe.throw(_("Bar ownership must match its refining batch"))
    if not batch.final_assay_confirmed:
        frappe.throw(_("Batch requires reconciled final assays before bar registration"))
    if not frappe.db.exists("Refining Batch Reconciliation",
                            {"refining_batch": batch.name, "docstatus": 1}):
        frappe.throw(_("Batch must be reconciled before bar registration"))
    if batch.weight_uom != doc.uom:
        frappe.throw(_("Bar weight UOM must equal batch weight UOM"))
    if doc.ownership == "Customer Owned":
        if not doc.owner_customer:
            frappe.throw(_("Customer-owned bar requires an owner customer"))
        for row in batch.inputs:
            lot = frappe.get_doc("Metal Lot", row.metal_lot)
            if lot.owner_party != doc.owner_customer or lot.ownership != "Customer Owned":
                frappe.throw(_("Bar owner must match every batch input lot"))
    elif doc.owner_customer:
        frappe.throw(_("Company-owned bars cannot have a customer owner"))
    positive(doc.weight, _("Bar gross weight"))
    doc.fine_weight = float(fine(doc.weight, doc.purity_percent))
    # Byproducts (e.g. Pd or Ag) must be supported by constituent assays;
    # do not treat the full gold feed weight as available palladium.
    from metal_refinery_tz.metal_refinery_tz.services.refining_rounds import require_final_outputs
    input_fine = decimal(0)
    for row in batch.inputs:
        if row.metal_type == doc.metal_type:
            input_fine += decimal(row.fine_weight)
        elif row.input_assay:
            assay = frappe.get_doc("Metal Assay", row.input_assay)
            component = next((r for r in assay.results if r.metal_type == doc.metal_type), None)
            if component:
                input_fine += fine(row.input_weight, component.purity_percent)
    finished_rows = [
        row for row in batch.outputs
        if row.output_type == "Finished Metal" and row.metal_type == doc.metal_type
    ]
    for output in finished_rows:
        if frappe.db.exists("Refining Batch Input", {"metal_lot": output.output_lot}):
            frappe.throw(_("Cannot register bars from an output already sent for further refining"))
    finished_fine = require_final_outputs(batch).get(doc.metal_type, decimal(0))
    available_fine = min(input_fine, finished_fine)
    if available_fine <= 0:
        frappe.throw(_("Batch has no available finished fine-metal weight for bars"))

    others = frappe.get_all(
        "Metal Bar Register",
        filters={"refining_batch": doc.refining_batch, "metal_type": doc.metal_type},
        fields=["name", "fine_weight"],
    )
    allocated = sum((decimal(row.fine_weight) for row in others if row.name != doc.name), decimal(0))
    requested = decimal(doc.fine_weight)
    # Six-decimal weights are the accounting precision in metal_math; do not
    # allow a one-micro-unit over-allocation through an extra tolerance.
    if allocated + requested > available_fine:
        frappe.throw(
            _("Total bar fine weight ({0}) exceeds available batch fine weight ({1}); already registered: {2}")
            .format(allocated + requested, available_fine, allocated)
        )
    if doc.warehouse and frappe.db.get_value("Warehouse", doc.warehouse, "company") != doc.company:
        frappe.throw(_("Bar warehouse belongs to another company"))
    old = doc.get_doc_before_save()
    if not old and doc.status != "In Vault":
        frappe.throw(_("Newly registered bars must start In Vault"))
    if old:
        for key in ("company", "bar_id", "refining_batch", "metal_type", "ownership",
                    "owner_customer", "weight", "purity_percent", "uom", "status"):
            if doc.get(key) != old.get(key):
                frappe.throw(_("Bar provenance and release status cannot be edited directly"))


def validate_export(doc):
    release = frappe.get_doc("Metal Release Authorization", doc.release_authorization)
    if release.docstatus != 1 or release.company != doc.company or release.customer != doc.customer:
        frappe.throw(_("Shipment requires matching submitted metal release"))
    if not doc.checklist:
        frappe.throw(_("Export compliance checklist is required"))
    seen = set()
    for row in doc.checklist:
        key = row.requirement.strip().lower()
        if key in seen:
            frappe.throw(_("Duplicate checklist requirement"))
        seen.add(key)
        if not row.verified or not row.evidence_reference or not row.verified_by:
            frappe.throw(_("Every compliance requirement must be verified with evidence"))
    for doctype, name in (("Sales Invoice", doc.sales_invoice), ("Delivery Note", doc.delivery_note)):
        if not name:
            continue
        reference = frappe.get_doc(doctype, name)
        if reference.company != doc.company or reference.customer != doc.customer:
            frappe.throw(_("{0} company or customer mismatch").format(doctype))
