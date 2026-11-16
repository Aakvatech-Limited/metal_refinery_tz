"""Static checks for Frappe app source files without needing a database."""
import ast
import json
import pathlib
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "metal_refinery_tz"
MODULE = PACKAGE / "metal_refinery_tz"
module_name = "Metal Refinery TZ"

for path in PACKAGE.rglob("*.py"):
    ast.parse(path.read_text(), filename=str(path))
for path in ROOT.rglob("*.json"):
    json.loads(path.read_text())

config = tomllib.loads((ROOT / "pyproject.toml").read_text())
assert config["project"]["name"] == "metal_refinery_tz"
assert config["tool"]["bench"]["frappe-dependencies"]["frappe"].startswith(">=16.")
assert config["tool"]["bench"]["frappe-dependencies"]["erpnext"].startswith(">=16.")
assert (PACKAGE / "modules.txt").read_text().strip() == module_name

doctypes = {}
for path in (MODULE / "doctype").glob("*/*.json"):
    data = json.loads(path.read_text())
    assert data["doctype"] == "DocType", path
    assert data["module"] == module_name, path
    assert len({f["fieldname"] for f in data["fields"]}) == len(data["fields"]), path
    assert set(data["field_order"]) == {f["fieldname"] for f in data["fields"]}, path
    assert not (data.get("autoname") or "").startswith("format:") or "{#####}" in data["autoname"], path
    # Frappe dynamically imports controllers for child tables during DocType sync.
    # An __init__.py alone is not sufficient; the DocType-named module must exist.
    controller = path.with_suffix(".py")
    assert controller.is_file(), f"Missing DocType controller: {controller}"
    expected_class = data["name"].replace(" ", "")
    module_ast = ast.parse(controller.read_text(), filename=str(controller))
    declared_classes = {node.name for node in module_ast.body if isinstance(node, ast.ClassDef)}
    assert expected_class in declared_classes, (
        f"Controller {controller} does not define {expected_class}"
    )
    # Layout contract: an ordinary DocType is organized into <= 3 columns per section.
    # Child-table list columns must be explicit and fit within Frappe's 10-unit grid.
    if data.get("istable"):
        visible = [f for f in data["fields"] if f.get("in_list_view")]
        assert 2 <= len(visible) <= 5, (path, "Expected 2-5 visible grid fields")
        assert sum(int(f.get("columns") or 2) for f in visible) <= 10, (
            path, "Child grid exceeds 10 width units"
        )
        assert all(not f.get("hidden") for f in visible), (path, "Hidden grid field")
    else:
        assert data["fields"] and data["fields"][0]["fieldtype"] == "Section Break", (
            path, "Parent form must start with a section"
        )
        columns = 0
        section_fields = []
        for f in data["fields"]:
            if f["fieldtype"] == "Section Break":
                if section_fields:
                    tables = [x for x in section_fields if x["fieldtype"] == "Table"]
                    assert not tables or len(section_fields) == 1, (
                        path, "Child table must occupy its own full-width section"
                    )
                section_fields = []
                columns = 1
                assert f.get("label"), (path, "Section needs a heading")
            elif f["fieldtype"] == "Column Break":
                columns += 1
                assert columns <= 3, (path, "More than three columns in section")
            else:
                section_fields.append(f)
        tables = [x for x in section_fields if x["fieldtype"] == "Table"]
        assert not tables or len(section_fields) == 1, (path, "Child table needs its own section")
    doctypes[data["name"]] = data

known = {
    "Company", "Customer", "Supplier", "User", "Warehouse", "UOM", "Currency",
    "Work Order", "Job Card", "BOM", "Purchase Invoice", "Sales Invoice",
    "Delivery Note", "Country", "Account", "Project", "Cost Center", "Item", "Purchase Receipt", "Stock Entry",
}
for name, data in doctypes.items():
    for field in data["fields"]:
        if field["fieldtype"] in ("Link", "Table"):
            assert field.get("options") in doctypes or field.get("options") in known, (name, field)

base = MODULE / "sidebar/metal_refinery_tz/metal_refinery_tz.json"
side = json.loads(base.read_text())
assert side["module"] == module_name and side["standard"] == 1
for item in side["items"]:
    if item.get("link_type") == "DocType":
        assert item["link_to"] in doctypes, item

workspace = json.loads((MODULE / "workspace/metal_refinery_tz/metal_refinery_tz.json").read_text())
assert workspace["standard"] == 1 and workspace["module"] == module_name
blocks = json.loads(workspace["content"])
cards = {json.loads(p.read_text())["name"] for p in (MODULE / "number_card").glob("*/*.json")}
charts = {json.loads(p.read_text())["name"] for p in (MODULE / "dashboard_chart").glob("*/*.json")}
for block in blocks:
    data = block.get("data") or {}
    if block["type"] == "number_card":
        assert data["number_card_name"] in cards, block
    if block["type"] == "chart":
        assert data["chart_name"] in charts, block

dash = json.loads((MODULE / "metal_refinery_tz_dashboard/metal_refinery_operations/metal_refinery_operations.json").read_text())
assert dash["is_standard"] == 1
assert all(x["chart"] in charts for x in dash["charts"])
assert all(x["card"] in cards for x in dash["cards"])
reports = {}
for path in (MODULE / "report").glob("*/*.json"):
    report = json.loads(path.read_text())
    assert report["doctype"] == "Report" and report["is_standard"] == "Yes", path
    assert report["module"] == module_name, path
    assert report["ref_doctype"] in doctypes, path
    stem = path.stem
    for ext in (".py", ".js"):
        assert path.with_suffix(ext).is_file(), (path, ext)
    reports[report["name"]] = report
for item in side["items"]:
    if item.get("link_type") == "Report":
        assert item["link_to"] in reports, item
for item in workspace["links"]:
    if item.get("link_type") == "Report":
        assert item["link_to"] in reports, item

# Navigation is complete only when every standalone record and report is reachable.
targets = {
    "DocType": {name for name, doc in doctypes.items() if not doc.get("istable")},
    "Report": set(reports),
    "Workspace": {workspace["name"]},
    "Dashboard": {dash["name"]},
}
for surface, rows in (("Sidebar", side["items"]), ("Workspace", workspace["links"])):
    linked = {}
    for row in rows:
        if row.get("link_to"):
            kind = row["link_type"]
            assert row["link_to"] in targets[kind], (surface, row)
            key = (kind, row["link_to"])
            assert key not in linked, (surface, "Duplicate navigation target", key)
            linked[key] = row
    for kind in ("DocType", "Report"):
        assert {name for k, name in linked if k == kind} == targets[kind], (surface, kind)

assert any(row.get("link_to") == dash["name"] for row in side["items"])
shortcuts = {row["label"]: row for row in workspace["shortcuts"]}
assert any(row["type"] == "Dashboard" and row["link_to"] == dash["name"]
           for row in shortcuts.values())
for block in blocks:
    if block["type"] == "shortcut":
        row = shortcuts[block["data"]["shortcut_name"]]
        assert row["link_to"] in targets[row["type"]], row

group = None
group_count = 0
group_labels = set()
for row in workspace["links"]:
    if row["type"] == "Card Break":
        if group:
            assert group["link_count"] == group_count, group
        group, group_count = row, 0
        group_labels.add(row["label"])
    else:
        group_count += 1
        if row["link_type"] == "Report":
            assert row["is_query_report"] == 1, row
            assert row["report_ref_doctype"] == reports[row["link_to"]]["ref_doctype"], row
assert group and group["link_count"] == group_count
assert {b["data"]["card_name"] for b in blocks if b["type"] == "card"} == group_labels

for kind, collection, field, names, folder in (
    ("number_card", "number_cards", "number_card_name", cards, "number_card"),
    ("chart", "charts", "chart_name", charts, "dashboard_chart"),
):
    assert {b["data"][field] for b in blocks if b["type"] == kind} == names
    assert {row[field] for row in workspace[collection]} == names
    dashboard_field = "card" if kind == "number_card" else "chart"
    assert {row[dashboard_field] for row in dash["cards" if kind == "number_card" else "charts"]} == names
    for path in (MODULE / folder).glob("*/*.json"):
        doc = json.loads(path.read_text())
        assert doc["is_standard"] == 1 and doc["module"] == module_name, path
        source = doctypes[doc["document_type"]]
        fields = {f["fieldname"] for f in source["fields"]} | {"docstatus"}
        filters = json.loads(doc["filters_json"])
        assert all(f[0] in fields for f in filters), path
        if kind == "chart":
            assert doc["group_by_based_on"] in fields, path
            assert ["docstatus", "!=", 2] in filters, path

dock = json.loads((PACKAGE / "dock/metal_refinery_tz/metal_refinery_tz.json").read_text())
assert dock["standard"] == 1 and dock["app"] == "metal_refinery_tz"
assert any(row["link_type"] == "Sidebar" and row["link_to"] == side["name"]
           for row in dock["items"])

print(f"OK: {len(doctypes)} DocTypes; {len(cards)} Cards; {len(charts)} Charts; all source links resolve")
