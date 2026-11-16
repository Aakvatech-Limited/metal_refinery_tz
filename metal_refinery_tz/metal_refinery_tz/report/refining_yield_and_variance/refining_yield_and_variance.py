"""Fine metal reconciliation by batch, using submitted source rows."""
import frappe
from frappe import _


def execute(filters=None):
    filters = frappe._dict(filters or {})
    if filters.get("from_date") and filters.get("to_date") and filters.from_date > filters.to_date:
        frappe.throw(_("From Date must not exceed To Date"))

    def c(label, t="Data", opt=None, width=115):
        return {"label": _(label), "fieldname": label.lower().replace(" (%)", "").replace(" ", "_"), "fieldtype": t,
                "options": opt, "width": width}

    columns = [
        c("Batch", "Link", "Refining Batch", 155), c("Round", "Int", width=75),
        c("Source Batches", width=170), c("Date", "Date", width=105),
        c("Company", "Link", "Company", 150), c("Metal", "Link", "Metal Type", 135),
        c("Ownership", width=130), c("UOM", "Link", "UOM", 75),
        c("Fine Input", "Float"), c("Finished Fine", "Float"), c("Residue Fine", "Float"),
        c("Loss Fine", "Float"), c("Other Fine", "Float"), c("Unaccounted", "Float"),
        c("Recovery (%)", "Percent"), c("Reconciliation", "Link", "Refining Batch Reconciliation", 155),
        c("Byproducts", width=210), c("Final Assays Confirmed", "Check", width=145),
        c("Status", width=130),
    ]
    conditions = {"docstatus": 1}
    for field in ("company", "metal_type", "ownership"):
        if filters.get(field):
            conditions[field] = filters[field]
    if filters.get("from_date") or filters.get("to_date"):
        conditions["batch_date"] = ["between", [
            filters.get("from_date") or "1900-01-01", filters.get("to_date") or "2999-12-31"
        ]]
    rows = frappe.get_list("Refining Batch", filters=conditions,
                          fields=["name", "batch_date", "company", "metal_type", "ownership",
                                  "weight_uom", "input_fine_weight", "unaccounted_fine_weight",
                                  "round_number", "final_assay_confirmed", "status"],
                          order_by="batch_date desc, name desc", limit_page_length=0)
    data = []
    for batch in rows:
        outputs = frappe.get_all("Refining Batch Output",
                                 filters={"parent": batch.name, "parenttype": "Refining Batch"},
                                 fields=["output_type", "metal_type", "fine_weight", "uom"], limit_page_length=0)
        totals = {"Finished Metal": 0.0, "Recoverable Residue": 0.0,
                  "Process Loss": 0.0, "Sample": 0.0, "Closing WIP": 0.0}
        byproducts = {}
        for o in outputs:
            if o.metal_type != batch.metal_type:
                if o.output_type not in ("Process Loss", "Sample"):
                    byproducts[o.metal_type] = byproducts.get(o.metal_type, 0) + float(o.fine_weight or 0)
            elif o.output_type in totals:
                totals[o.output_type] += float(o.fine_weight or 0)
        links = frappe.get_all("Refining Batch Input",
                               filters={"parent": batch.name, "parenttype": "Refining Batch"},
                               fields=["metal_lot"], limit_page_length=0)
        sources = sorted({
            src for row in links
            if (src := frappe.db.get_value("Metal Lot", row.metal_lot, "source_refining_batch"))
        })
        fine_input = float(batch.input_fine_weight or 0)
        reconciliations = frappe.get_all(
            "Refining Batch Reconciliation",
            filters={"refining_batch": batch.name, "docstatus": 1},
            fields=["name"], limit_page_length=1,
        )
        data.append({
            "batch": batch.name, "round": batch.round_number or 1,
            "source_batches": ", ".join(sources),
            "date": batch.batch_date, "company": batch.company,
            "metal": batch.metal_type, "ownership": batch.ownership, "uom": batch.weight_uom,
            "fine_input": fine_input, "finished_fine": totals["Finished Metal"],
            "residue_fine": totals["Recoverable Residue"], "loss_fine": totals["Process Loss"],
            "other_fine": totals["Sample"] + totals["Closing WIP"],
            "unaccounted": batch.unaccounted_fine_weight,
            "recovery": round(totals["Finished Metal"] / fine_input * 100, 4) if fine_input else None,
            "reconciliation": reconciliations[0].name if reconciliations else None,
            "byproducts": "; ".join(f"{metal}: {qty:.6f}" for metal, qty in sorted(byproducts.items())),
            "final_assays_confirmed": batch.final_assay_confirmed or 0,
            "status": batch.status,
        })
    return columns, data
