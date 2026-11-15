"""Frappe application hooks for Metal Refinery TZ.

The app starts with no custom documents, exports or patches.
Declare app navigation only after the corresponding standard Workspace exists.
"""

app_name = "metal_refinery_tz"
app_title = "Metal Refinery TZ"
app_publisher = "Aakvatech Limited"
app_description = "Operational traceability and controls for precious metal refineries"
app_email = "info@aakvatech.com"
app_license = "mit"
required_apps = ["erpnext"]

# v16 app entry / Dock / Sidebars / Workspaces will be exported together
# once a live development-mode site validates their native schemas.
