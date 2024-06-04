import json

DASHBOARD_PATH = "grafana/provisioning/dashboards/nethermind.json"
NEW_DASHBOARD_PATH = "temp/dashboard.json"

NETH_DASHBOARD_TITLE = "Nethermind Dashboard"
NETH_DASHBOARD_UID = "nethermind_dashboard"


def update_dashboard():
    with open(DASHBOARD_PATH, "r") as f:
        old_dashboard: dict[str] = json.load(f)

    with open(NEW_DASHBOARD_PATH, "r") as f:
        dashboard: dict[str] = json.load(f)

    # Update constants
    ## Name
    dashboard["title"] = NETH_DASHBOARD_TITLE
    ## UID
    dashboard["uid"] = NETH_DASHBOARD_UID
    ## Version
    dashboard["version"] = old_dashboard.get("version", 0) + 1
    ## Deselect variables
    for variable in dashboard["templating"]["list"]:
        if "current" in variable:
            if "selected" in variable["current"]:
                variable["current"]["selected"] = False

    with open(DASHBOARD_PATH, "w") as f:
        json.dump(dashboard, f, indent=2)


if __name__ == "__main__":
    update_dashboard()
