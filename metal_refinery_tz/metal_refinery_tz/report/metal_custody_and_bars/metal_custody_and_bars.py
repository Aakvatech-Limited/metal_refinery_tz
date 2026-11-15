"""Operational custody snapshot. NOT a stock ledger or financial stock valuation."""
import frappe
from frappe import _


def execute(filters=None):
    filters = frappe._dict(filters or {})

    def c(label, t="Data", opt=None, width=130):
        return {"label": _(label), "fieldname": label.lower().replace(" (%)", "").replace(" ", "_"), "fieldtype": t,
                "options": opt, "width": width}

    columns = [
        c("Record Type", width=110), c("Reference", width=160),
        c("Company", "Link", "Company", 150), c("Ownership", width=135),
        c("Customer", "Link", "Customer", 180), c("Metal", "Link", "Metal Type", 135),
        c("Warehouse", "Link", "Warehouse", 180), c("UOM", "Link", "UOM", 90),
        c("Weight", "Float", width=110), c("Purity (%)", "Percent", width=105),
        c("Fine Weight", "Float", width=115), c("Status", width=125),
        c("Source", width=155),
    ]
    conditions = {}
    for field in ("company", "ownership", "metal_type", "warehouse"):
        if filters.get(field):
            conditions[field] = filters[field]
    records = []
    lots = frappe.get_list("Metal Lot", filters=conditions,
                          fields=["name", "company", "ownership", "owner_party", "owner_party_type",
                                  "metal_type", "warehouse", "uom", "initial_weight", "status", "intake"],
                          limit_page_length=0)
    for lot in lots:
        if filters.get("customer") and lot.owner_party != filters.customer:
            continue
        records.append({
            "record_type": _("Intake Lot"), "reference": lot.name, "company": lot.company,
            "ownership": lot.ownership,
            "customer": lot.owner_party if lot.owner_party_type == "Customer" else None,
            "metal": lot.metal_type, "warehouse": lot.warehouse, "uom": lot.uom,
            "weight": lot.initial_weight, "purity": None, "fine_weight": None,
            "status": lot.status, "source": lot.intake,
        })
    bar_filters = {}
    for field in ("company", "ownership", "metal_type", "warehouse"):
        if filters.get(field):
            bar_filters[field] = filters[field]
    if filters.get("customer"):
        bar_filters["owner_customer"] = filters.customer
    bars = frappe.get_list("Metal Bar Register", filters=bar_filters,
                          fields=["name", "company", "ownership", "owner_customer", "metal_type",
                                  "warehouse", "uom", "weight", "purity_percent", "fine_weight",
                                  "status", "refining_batch"], limit_page_length=0)
    for bar in bars:
        records.append({
            "record_type": _("Registered Bar"), "reference": bar.name, "company": bar.company,
            "ownership": bar.ownership, "customer": bar.owner_customer, "metal": bar.metal_type,
            "warehouse": bar.warehouse, "uom": bar.uom, "weight": bar.weight,
            "purity": bar.purity_percent, "fine_weight": bar.fine_weight,
            "status": bar.status, "source": bar.refining_batch,
        })
    return columns, records
