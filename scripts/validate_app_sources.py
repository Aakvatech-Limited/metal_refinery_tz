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
    expected_class = "".join(part.title() for part in path.stem.split("_"))
    module_ast = ast.parse(controller.read_text(), filename=str(controller))
    declared_classes = {node.name for node in module_ast.body if isinstance(node, ast.ClassDef)}
    assert expected_class in declared_classes, (
        f"Controller {controller} does not define {expected_class}"
    )
    doctypes[data["name"]] = data

known = {
    "Company", "Customer", "Supplier", "User", "Warehouse", "UOM", "Currency",
    "Work Order", "Job Card", "BOM", "Purchase Invoice", "Sales Invoice",
    "Delivery Note", "Country",
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
print(f"OK: {len(doctypes)} DocTypes; {len(cards)} Cards; {len(charts)} Charts; all source links resolve")
