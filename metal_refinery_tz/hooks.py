"""Metal Refinery TZ hooks."""
app_name = "metal_refinery_tz"
app_title = "Metal Refinery TZ"
app_publisher = "Aakvatech Limited"
app_description = "Traceability and operational controls for precious metal refineries"
app_email = "info@aakvatech.com"
app_license = "mit"
required_apps = ["erpnext"]
app_logo_url = "/assets/metal_refinery_tz/images/metal_refinery_tz.svg"
app_home = "/desk/metal-refinery-tz"

add_to_apps_screen = [
    {
        "name": app_name,
        "logo": app_logo_url,
        "title": app_title,
        "route": app_home,
        "sequence_id": 30,
    }
]

# Only refinery-linked PRs trigger invoice drafts; unrelated ERPNext PRs are unaffected.
doc_events = {
    "Purchase Receipt": {
        "on_submit": "metal_refinery_tz.metal_refinery_tz.services.posting_bridge.create_purchase_invoice_after_receipt"
    }
}
