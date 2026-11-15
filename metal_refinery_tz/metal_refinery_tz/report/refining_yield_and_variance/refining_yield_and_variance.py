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
        c("Batch", "Link", "Refining Batch", 155), c("Date", "Date", width=105),
        c("Company", "Link", "Company", 150), c("Metal", "Link", "Metal Type", 135),
        c("Ownership", width=130), c("UOM", "Link", "UOM", 75),
        c("Fine Input", "Float"), c("Finished Fine", "Float"), c("Residue Fine", "Float"),
        c("Loss Fine", "Float"), c("Other Fine", "Float"), c("Unaccounted", "Float"),
        c("Recovery (%)", "Percent"), c("Reconciliation", "Link", "Refining Batch Reconciliation", 155),
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
                                  "weight_uom", "input_fine_weight", "unaccounted_fine_weight", "status"],
                          order_by="batch_date desc, name desc", limit_page_length=0)
    data = []
    for batch in rows:
        outputs = frappe.get_all("Refining Batch Output",
                                 filters={"parent": batch.name, "parenttype": "Refining Batch"},
                                 fields=["output_type", "fine_weight"], limit_page_length=0)
        totals = {"Finished Metal": 0.0, "Recoverable Residue": 0.0,
                  "Process Loss": 0.0, "Sample": 0.0, "Closing WIP": 0.0}
        for o in outputs:
            if o.output_type in totals:
                totals[o.output_type] += float(o.fine_weight or 0)
        fine_input = float(batch.input_fine_weight or 0)
        reconciliations = frappe.get_all(
            "Refining Batch Reconciliation",
            filters={"refining_batch": batch.name, "docstatus": 1},
            fields=["name"], limit_page_length=1,
        )
        data.append({
            "batch": batch.name, "date": batch.batch_date, "company": batch.company,
            "metal": batch.metal_type, "ownership": batch.ownership, "uom": batch.weight_uom,
            "fine_input": fine_input, "finished_fine": totals["Finished Metal"],
            "residue_fine": totals["Recoverable Residue"], "loss_fine": totals["Process Loss"],
            "other_fine": totals["Sample"] + totals["Closing WIP"],
            "unaccounted": batch.unaccounted_fine_weight,
            "recovery": round(totals["Finished Metal"] / fine_input * 100, 4) if fine_input else None,
            "reconciliation": reconciliations[0].name if reconciliations else None,
            "status": batch.status,
        })
    return columns, data
