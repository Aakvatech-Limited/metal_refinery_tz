"""Register palladium as an ordinary, configurable recoverable metal."""
import frappe


def execute():
    if not frappe.db.exists("Metal Type", "Palladium"):
        frappe.get_doc({
            "doctype": "Metal Type",
            "metal_name": "Palladium",
            "symbol": "Pd",
            "is_active": 1,
        }).insert(ignore_permissions=True)
