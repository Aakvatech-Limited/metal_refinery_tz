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

    # Historical batches predate the round-number field and are first rounds.
    for batch in frappe.get_all(
        "Refining Batch", fields=["name", "round_number"], limit_page_length=0
    ):
        if not batch.round_number:
            frappe.db.set_value(
                "Refining Batch", batch.name, "round_number", 1, update_modified=False
            )
