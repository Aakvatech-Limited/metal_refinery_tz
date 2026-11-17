"""Opt-in, DRAFT-ONLY ERPNext finance and material staging bridge.

No stock ledger, GL posting or invoice submission occurs here. This module
must not be used as an automatic metal valuation / manufacture engine.
"""
from collections import defaultdict
from decimal import Decimal

import frappe
from frappe import _
from frappe.utils import flt, today

from metal_refinery_tz.metal_refinery_tz.services.metal_math import decimal, positive


def _company_link(doctype, name, company):
    if name and frappe.db.get_value(doctype, name, "company") != company:
        frappe.throw(_("{0} {1} must belong to company {2}").format(doctype, name, company))


def _item(item_code, must_be_stock):
    if not item_code:
        frappe.throw(_("A mapped ERPNext item is required before creating drafts"))
    doc = frappe.get_doc("Item", item_code)
    if bool(doc.is_stock_item) != bool(must_be_stock):
        frappe.throw(_("Item {0} stock/service classification is incompatible").format(item_code))
    if doc.disabled:
        frappe.throw(_("Mapped ERPNext Item is disabled: {0}").format(item_code))
    return doc


def validate_profile(doc):
    _company_link("Cost Center", doc.cost_center, doc.company)
    _company_link("Project", doc.project, doc.company)
    for warehouse in ("receipt_warehouse", "wip_warehouse", "finished_warehouse"):
        _company_link("Warehouse", doc.get(warehouse), doc.company)
    for field in ("expense_account", "income_account"):
        _company_link("Account", doc.get(field), doc.company)
    seen = set()
    for row in doc.get("metal_item_mappings") or []:
        if row.metal_type in seen:
            frappe.throw(_("Duplicate metal type in ERPNext Item Mapping: {0}").format(row.metal_type))
        seen.add(row.metal_type)
        _item(row.raw_material_item, True)
        for item_name in ("finished_metal_item", "residue_item"):
            if row.get(item_name):
                _item(row.get(item_name), True)
    if doc.toll_service_item:
        _item(doc.toll_service_item, False)
    if doc.auto_create_drafts:
        if not doc.expense_account or not doc.income_account:
            frappe.throw(_("Explicit company expense and income accounts are required to enable drafts"))
        if not doc.cost_center:
            frappe.throw(_("Default cost center is mandatory for automatic draft generation"))


def get_enabled_profile(company):
    name = frappe.db.get_value("Metal ERPNext Posting Profile", {"company": company}, "name")
    if not name:
        return None
    profile = frappe.get_doc("Metal ERPNext Posting Profile", name)
    return profile if profile.auto_create_drafts else None


def _raw_item_for_metal(profile, metal_type):
    matching = [r for r in profile.metal_item_mappings if r.metal_type == metal_type]
    if len(matching) != 1:
        frappe.throw(_("Exactly one ERPNext item mapping is needed for {0}").format(metal_type))
    return _item(matching[0].raw_material_item, True)


def _check_company_currency(company, currency):
    base = frappe.db.get_value("Company", company, "default_currency")
    if base != currency:
        frappe.throw(_("Multi-currency metal posting is not configured; expected {0}").format(base))


def _source_stamp(doctype, name, purpose):
    return "METAL_REFINERY_TZ | {0} | {1} | {2}".format(doctype, name, purpose)


def create_purchase_receipt_draft(settlement):
    profile = get_enabled_profile(settlement.company)
    if not profile:
        return
    if settlement.purchase_receipt:
        return
    intake = frappe.get_doc("Metal Intake", settlement.metal_intake)
    if intake.ownership != "Company Owned" or intake.party_type != "Supplier":
        frappe.throw(_("Only supplier-owned purchase intakes can generate purchase receipts"))
    _check_company_currency(settlement.company, settlement.currency)
    # Deductions require explicitly modeled charge accounts: netting them against
    # the metal rate would silently distort inventory valuation and supplier costs.
    if decimal(settlement.total_deductions) != 0:
        frappe.throw(_("Automatic procurement draft requires zero settlement deductions; "
                       "allocate deduction accounts in an approved costing design first"))
    item = _raw_item_for_metal(profile, settlement.metal_type)
    if item.stock_uom != intake.uom:
        frappe.throw(_("Purchase item stock UOM must equal intake UOM: {0}").format(intake.uom))
    warehouse = profile.receipt_warehouse or intake.warehouse
    _company_link("Warehouse", warehouse, settlement.company)
    positive(intake.net_weight, _("Intake gross metal weight"))
    rate = decimal(settlement.net_amount) / decimal(intake.net_weight)
    receipt = frappe.get_doc({
        "doctype": "Purchase Receipt",
        "company": settlement.company,
        "supplier": intake.party,
        "posting_date": intake.posting_date,
        "set_warehouse": warehouse,
        "cost_center": profile.cost_center,
        "project": profile.project,
        "remarks": _source_stamp("Metal Purchase Settlement", settlement.name, "RECEIPT"),
        "items": [{
            "item_code": item.name, "qty": flt(intake.net_weight),
            "rate": float(rate), "warehouse": warehouse,
            "cost_center": profile.cost_center, "project": profile.project,
            "description": "Refinery intake {0}; lot {1}; assay {2}".format(
                intake.name, intake.metal_lot, settlement.assay),
        }],
    })
    receipt.insert(ignore_permissions=True)
    frappe.db.set_value("Metal Purchase Settlement", settlement.name,
                        "purchase_receipt", receipt.name, update_modified=False)


def create_purchase_invoice_after_receipt(receipt, method=None):
    """After an authorized PR submit, prepare exactly one unsubmitted PI."""
    settlements = frappe.get_all(
        "Metal Purchase Settlement",
        filters={"purchase_receipt": receipt.name, "docstatus": 1},
        fields=["name", "purchase_invoice"], limit_page_length=2,
    )
    if not settlements:
        return
    if len(settlements) != 1:
        frappe.throw(_("One Purchase Receipt may only represent one metal settlement"))
    settlement = frappe.get_doc("Metal Purchase Settlement", settlements[0].name)
    if settlement.purchase_invoice:
        return
    profile = get_enabled_profile(settlement.company)
    if not profile:
        return
    if receipt.docstatus != 1:
        frappe.throw(_("Purchase Receipt must be submitted before Purchase Invoice generation"))
    _check_company_currency(settlement.company, settlement.currency)
    intake = frappe.get_doc("Metal Intake", settlement.metal_intake)
    if len(receipt.items) != 1 or decimal(receipt.items[0].qty) != decimal(intake.net_weight):
        frappe.throw(_("Metal Purchase Receipt item quantities changed; invoice draft blocked"))
    row = receipt.items[0]
    invoice = frappe.get_doc({
        "doctype": "Purchase Invoice", "company": settlement.company,
        "supplier": intake.party, "posting_date": today(),
        "update_stock": 0, "cost_center": profile.cost_center,
        "project": profile.project,
        "remarks": _source_stamp("Metal Purchase Settlement", settlement.name, "INVOICE"),
        "items": [{
            "item_code": row.item_code, "qty": row.qty, "rate": row.rate,
            "purchase_receipt": receipt.name, "pr_detail": row.name,
            "cost_center": profile.cost_center, "project": profile.project,
            "description": "Refinery settlement {0}".format(settlement.name),
        }],
    })
    invoice.insert(ignore_permissions=True)
    frappe.db.set_value("Metal Purchase Settlement", settlement.name,
                        "purchase_invoice", invoice.name, update_modified=False)


def create_toll_sales_invoice_draft(job):
    profile = get_enabled_profile(job.company)
    if not profile or job.sales_invoice:
        return
    _check_company_currency(job.company, job.currency)
    item = _item(profile.toll_service_item, False)
    positive(job.service_fee, _("Toll refining service fee"))
    row = {
        "item_code": item.name, "qty": 1, "rate": flt(job.service_fee),
        "cost_center": profile.cost_center, "project": profile.project,
        "description": "Toll refining job {0}, intake {1}, batch {2}".format(
            job.name, job.metal_intake, job.refining_batch),
    }
    if profile.income_account:
        row["income_account"] = profile.income_account
    invoice = frappe.get_doc({
        "doctype": "Sales Invoice", "company": job.company, "customer": job.customer,
        "posting_date": today(), "currency": job.currency, "update_stock": 0,
        "cost_center": profile.cost_center, "project": profile.project,
        "remarks": _source_stamp("Toll Refining Job", job.name, "SERVICE_INVOICE"),
        "items": [row],
    })
    invoice.insert(ignore_permissions=True)
    frappe.db.set_value("Toll Refining Job", job.name, "sales_invoice",
                        invoice.name, update_modified=False)


def validate_operating_costs(batch):
    for row in batch.get("operating_costs") or []:
        positive(row.qty, _("Operating cost quantity"))
        if decimal(row.rate) < 0:
            frappe.throw(_("Operating cost rate cannot be negative"))
        if not row.supplier or not row.item_code:
            frappe.throw(_("Operating costs require Supplier and Item"))
        _item(row.item_code, False)
        if row.cost_center:
            _company_link("Cost Center", row.cost_center, batch.company)
        if row.project:
            _company_link("Project", row.project, batch.company)
        row.amount = flt(decimal(row.qty) * decimal(row.rate))


def create_operating_cost_invoices(batch):
    profile = get_enabled_profile(batch.company)
    if not profile or not batch.get("operating_costs"):
        return
    groups = defaultdict(list)
    for row in batch.operating_costs:
        if row.purchase_invoice:
            continue
        groups[row.supplier].append(row)
    for supplier, rows in groups.items():
        lines = []
        for r in rows:
            line = {
                "item_code": r.item_code, "qty": r.qty, "rate": r.rate,
                "cost_center": r.cost_center or profile.cost_center,
                "project": r.project or profile.project,
                "description": r.description or "Operating cost for refining batch {0}".format(batch.name),
            }
            if profile.expense_account:
                line["expense_account"] = profile.expense_account
            lines.append(line)
        inv = frappe.get_doc({
            "doctype": "Purchase Invoice", "company": batch.company,
            "supplier": supplier, "posting_date": today(),
            "update_stock": 0, "cost_center": profile.cost_center,
            "project": profile.project,
            "remarks": _source_stamp("Refining Batch", batch.name, "OPERATING_COST:{0}".format(supplier)),
            "items": lines,
        })
        inv.insert(ignore_permissions=True)
        for r in rows:
            frappe.db.set_value("Metal Operation Cost", r.name, "purchase_invoice",
                                inv.name, update_modified=False)


def create_wip_transfer_draft(batch):
    """Only a draft raw-metal movement; NOT manufacture or finished metal receipt."""
    profile = get_enabled_profile(batch.company)
    if not profile or batch.stock_entry or batch.ownership != "Company Owned":
        return
    if not profile.wip_warehouse:
        return  # A WIP transfer is not configured.
    _company_link("Warehouse", profile.wip_warehouse, batch.company)
    item = _raw_item_for_metal(profile, batch.metal_type)
    if item.stock_uom != batch.weight_uom:
        frappe.throw(_("Batch and ERPNext stock item must use the same UOM"))
    # Repeat refining represents existing WIP, not a new raw-metal receipt.
    if any(frappe.db.get_value("Metal Lot", r.metal_lot, "source_refining_batch") for r in batch.inputs):
        return
    rows = []
    for input_row in batch.inputs:
        lot = frappe.get_doc("Metal Lot", input_row.metal_lot)
        if lot.ownership != "Company Owned":
            frappe.throw(_("Cannot stock-transfer customer-owned metal"))
        if lot.warehouse == profile.wip_warehouse:
            frappe.throw(_("WIP destination cannot equal the input warehouse"))
        settlements = frappe.get_all(
            "Metal Purchase Settlement",
            filters={"metal_intake": lot.intake, "docstatus": 1},
            fields=["purchase_receipt"], limit_page_length=1,
        )
        if not settlements or not settlements[0].purchase_receipt or (
            frappe.db.get_value("Purchase Receipt", settlements[0].purchase_receipt, "docstatus") != 1
        ):
            return  # No stock ledger receipt yet; do not fabricate a transferable balance.
        rows.append({
            "item_code": item.name, "qty": input_row.input_weight,
            "s_warehouse": lot.warehouse, "t_warehouse": profile.wip_warehouse,
            "cost_center": profile.cost_center, "project": profile.project,
            "description": "Metal lot {0} / batch {1}".format(lot.name, batch.name),
        })
    entry = frappe.get_doc({
        "doctype": "Stock Entry", "stock_entry_type": "Material Transfer",
        "purpose": "Material Transfer", "company": batch.company,
        "cost_center": profile.cost_center, "project": profile.project,
        "remarks": _source_stamp("Refining Batch", batch.name, "WIP_TRANSFER"),
        "items": rows,
    })
    entry.insert(ignore_permissions=True)
    frappe.db.set_value("Refining Batch", batch.name, "stock_entry",
                        entry.name, update_modified=False)


def block_cancel_if_linked(doctype, links):
    """Prevent source cancellation until ERPNext references are explicitly reconciled."""
    for target in set(name for name in links if name):
        if frappe.db.exists(doctype, target):
            frappe.throw(_("Cannot cancel while linked {0} {1} exists. "
                           "Review, cancel and unlink the ERPNext document first.").format(
                doctype, target
            ))
