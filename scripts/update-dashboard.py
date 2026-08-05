#!/usr/bin/env python3
"""Sanitize a Grafana dashboard export before vendoring it into this repo."""

import argparse
import json
import re
import sys
from pathlib import Path

DASHBOARD_PATH = Path("grafana/provisioning/dashboards/nethermind.json")
EXPORT_PATH = Path("temp/dashboard.json")

DASHBOARD_TITLE = "Nethermind Dashboard"
DASHBOARD_NAME = "nethermind_dashboard"

LOCAL_DATASOURCES = {
    "prometheus_ds": {"text": "Prometheus", "value": "prometheus_ds"},
    "loki_ds": {"text": "Loki", "value": "loki_ds"},
}

ALL_SELECTED = {"text": "All", "value": ["$__all"]}
NONE_SELECTED_MULTI = {"text": [], "value": []}
NONE_SELECTED = {"text": "", "value": ""}

INTERNAL_PATTERNS = {
    "Grafana Cloud stack namespace": re.compile(r"stacks-\d+"),
    "identity provider user id": re.compile(r"(?:scim|okta|auth0)-[A-Za-z0-9]{6,}"),
    "internal resource annotation": re.compile(r"grafana\.app/(?:updatedBy|updatedTimestamp|saved-from-ui|deprecatedInternalID)"),
    "Grafana Cloud plugin build id": re.compile(r"\d+\.\d+\.\d+-\d{5,}"),
}

CLOUD_BUILD_SUFFIX = re.compile(r"-\d{5,}$")

# Every datasource must resolve through a dashboard variable so the vendored
# dashboard binds to the local Prometheus/Loki instead of a Cloud datasource uid.
ALLOWED_DATASOURCE_REF = re.compile(r"^(\$\{?\w+\}?|grafana)$")


def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def load_export(path):
    try:
        export = json.loads(path.read_text())
    except FileNotFoundError:
        sys.exit(f"export not found: {path}")
    except json.JSONDecodeError as error:
        sys.exit(f"export is not valid JSON ({path}): {error}")

    api_version = export.get("apiVersion", "")
    if export.get("kind") != "Dashboard" or not api_version.startswith("dashboard.grafana.app/v2"):
        found = f"{api_version or '?'}/{export.get('kind') or '?'}"
        hint = (
            "fetch the v2 resource: "
            "GET <grafana>/apis/dashboard.grafana.app/v2/namespaces/<stack>/dashboards/<name>"
        )
        if "dashboard" in export or "panels" in export:
            hint = f"this looks like a classic dashboard export; {hint}"
        sys.exit(f"unexpected export shape ({found}): {hint}")

    if "elements" not in export.get("spec", {}):
        sys.exit("export has no spec.elements — not a v2 dashboard spec")

    return export


def reset_variables(spec):
    for variable in spec.get("variables", []):
        kind = variable.get("kind", "")
        variable_spec = variable.setdefault("spec", {})
        name = variable_spec.get("name", "")

        if "options" in variable_spec:
            variable_spec["options"] = []

        if kind == "DatasourceVariable":
            default = LOCAL_DATASOURCES.get(name)
            if default is None:
                print(f"warning: no local default for datasource variable {name!r}", file=sys.stderr)
            variable_spec["current"] = dict(default or NONE_SELECTED)
        elif variable_spec.get("includeAll"):
            variable_spec["current"] = dict(ALL_SELECTED)
        elif variable_spec.get("multi"):
            variable_spec["current"] = {"text": [], "value": []}
        elif "current" in variable_spec:
            variable_spec["current"] = dict(NONE_SELECTED)

        if kind not in ("DatasourceVariable", "QueryVariable", "TextVariable", "CustomVariable",
                        "ConstantVariable", "IntervalVariable"):
            print(f"warning: unhandled variable kind {kind!r} ({name}) — check it for internal values",
                  file=sys.stderr)


def normalize_plugin_versions(spec):
    """Drop the Cloud build suffix ("13.2.0-30402795349") but keep the plugin
    version itself — Grafana uses it to decide which panel migrations to run."""
    for node in walk(spec):
        if node.get("kind") == "VizConfig" and isinstance(node.get("version"), str):
            node["version"] = CLOUD_BUILD_SUFFIX.sub("", node["version"])


def drop_angular_leftovers(spec):
    for node in walk(spec):
        for key in [key for key in node if key.startswith("$$hash")]:
            del node[key]
    for node in walk(spec):
        if node.get("legacyOptions") == {}:
            del node["legacyOptions"]


def check_datasource_refs(export):
    offenders = set()
    for node in walk(export):
        datasource = node.get("datasource")
        if not isinstance(datasource, dict):
            continue
        ref = datasource.get("name") or datasource.get("uid") or ""
        if not ALLOWED_DATASOURCE_REF.match(str(ref)):
            offenders.add(str(ref))
    if offenders:
        sys.exit(
            "hardcoded datasource reference(s) found: "
            + ", ".join(sorted(offenders))
            + " — point the panel at ${prometheus_ds} / ${loki_ds} in Grafana and re-run"
        )


def check_no_internal_data(payload):
    findings = []
    for label, pattern in INTERNAL_PATTERNS.items():
        matches = sorted(set(pattern.findall(payload)))
        if matches:
            findings.append(f"{label}: {', '.join(str(match) for match in matches)}")
    if findings:
        sys.exit("internal data left in the dashboard:\n  " + "\n  ".join(findings))


def update_dashboard(export_path, output_path):
    export = load_export(export_path)
    spec = export["spec"]

    export.pop("status", None)
    export["metadata"] = {"name": DASHBOARD_NAME}
    spec["title"] = DASHBOARD_TITLE

    reset_variables(spec)
    normalize_plugin_versions(spec)
    drop_angular_leftovers(spec)
    check_datasource_refs(export)

    payload = json.dumps(export, indent=2, sort_keys=True) + "\n"
    check_no_internal_data(payload)
    output_path.write_text(payload)

    print(f"wrote {output_path} ({len(spec['elements'])} panels, {len(spec.get('variables', []))} variables)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", type=Path, default=EXPORT_PATH, help="fetched dashboard export")
    parser.add_argument("--output", type=Path, default=DASHBOARD_PATH, help="vendored dashboard file")
    args = parser.parse_args()
    update_dashboard(args.export, args.output)


if __name__ == "__main__":
    main()
