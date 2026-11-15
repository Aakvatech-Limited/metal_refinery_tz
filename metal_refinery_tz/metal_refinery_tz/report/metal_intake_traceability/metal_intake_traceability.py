"""Intake → lot → final assay → settlement → refining batch traceability."""
import frappe
from frappe import _


def execute(filters=None):
    filters = frappe._dict(filters or {})
    if filters.get("from_date") and filters.get("to_date") and filters.from_date > filters.to_date:
        frappe.throw(_("From Date must not exceed To Date"))

    def col(label, fieldtype="Data", options=None, width=130):
        return {"label": _(label), "fieldname": label.lower().replace(" (%)", "").replace(" ", "_"), "fieldtype": fieldtype,
                "options": options, "width": width}

    columns = [
        col("Intake", "Link", "Metal Intake", 155), col("Date", "Date", width=105),
        col("Company", "Link", "Company", 150), col("Party Type", width=105),
        col("Party", width=175), col("Ownership", width=135),
        col("Metal", "Link", "Metal Type", 135), col("Lot", "Link", "Metal Lot", 155),
        col("Net Weight", "Float", width=115), col("UOM", "Link", "UOM", 90),
        col("Assay", "Link", "Metal Assay", 155), col("Purity (%)", "Percent", width=105),
        col("Fine Weight", "Float", width=120),
        col("Purchase Settlement", "Link", "Metal Purchase Settlement", 165),
        col("Batch", "Link", "Refining Batch", 155),
    ]
    conditions = {"docstatus": 1}
    for field in ("company", "ownership", "metal_type"):
        if filters.get(field):
            conditions[field] = filters[field]
    if filters.get("from_date") or filters.get("to_date"):
        conditions["posting_date"] = ["between", [
            filters.get("from_date") or "1900-01-01", filters.get("to_date") or "2999-12-31"
        ]]
    intakes = frappe.get_list(
        "Metal Intake", filters=conditions,
        fields=["name", "posting_date", "company", "party_type", "party", "ownership",
                "metal_type", "net_weight", "uom", "metal_lot"],
        order_by="posting_date desc, name desc", limit_page_length=0,
    )
    data = []
    for intake in intakes:
        assay_filters = {"metal_intake": intake.name, "docstatus": 1, "assay_status": "Final"}
        assays = frappe.get_all("Metal Assay", filters=assay_filters, fields=["name", "sample_weight"],
                               order_by="modified desc", limit_page_length=0)
        # Do not silently choose a stale assay that has been superseded.
        superseded = {
            x.supersedes for x in frappe.get_all(
                "Metal Assay",
                filters={"metal_intake": intake.name, "docstatus": 1, "assay_status": "Final"},
                fields=["supersedes"], limit_page_length=0,
            ) if x.supersedes
        }
        assay_id = next((a.name for a in assays if a.name not in superseded and frappe.has_permission("Metal Assay", "read", a.name)), None)
        purity = None
        fine = None
        if assay_id:
            result = frappe.get_all("Metal Assay Result", filters={
                "parent": assay_id, "parenttype": "Metal Assay", "metal_type": intake.metal_type
            }, fields=["purity_percent"], limit_page_length=1)
            if result:
                purity = result[0].purity_percent
                fine = round(float(intake.net_weight or 0) * float(purity) / 100, 6)
        settlement = frappe.get_all("Metal Purchase Settlement",
                                   filters={"metal_intake": intake.name, "docstatus": 1},
                                   fields=["name"], limit_page_length=1)
        batch_rows = frappe.get_all("Refining Batch Input",
                                   filters={"metal_lot": intake.metal_lot},
                                   fields=["parent"], limit_page_length=0) if intake.metal_lot else []
        batch_ids = [
            r.parent for r in batch_rows
            if frappe.db.get_value("Refining Batch", r.parent, "docstatus") == 1
        ]
        linked_batches = batch_ids or [None]
        for batch in linked_batches:
            data.append({
                "intake": intake.name, "date": intake.posting_date,
                "company": intake.company, "party_type": intake.party_type,
                "party": intake.party, "ownership": intake.ownership,
                "metal": intake.metal_type, "lot": intake.metal_lot,
                "net_weight": intake.net_weight, "uom": intake.uom,
                "assay": assay_id, "purity": purity, "fine_weight": fine,
                "purchase_settlement": settlement[0].name if settlement else None,
                "batch": batch,
            })
    return columns, data
