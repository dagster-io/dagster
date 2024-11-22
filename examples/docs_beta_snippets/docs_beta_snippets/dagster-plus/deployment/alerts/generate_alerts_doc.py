# This script is used to generate content in `alerts.md`. It creates and formats the cross-product
# of all alert types and notification services. After adding a new alert type or service, just run
# `python generate_alerts_doc.py` and the corresponding markdown file will be updated.
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, NamedTuple, Optional

import yaml


class NotificationService(NamedTuple):
    name: str
    label: str
    effect_description: str
    config_snippet: Mapping[str, Any]
    setup_prose: str


class AlertType(NamedTuple):
    condition_description: str
    mdx_prose: str
    ui_label: str
    alert_name: str
    event_types: Sequence[str]
    config_snippet: Optional[Mapping[str, Any]]
    ui_prose: Optional[str] = None


BASE_PATH = "dagster-plus/deployment/alerts"
DOCS_PATH = Path(__file__).parent.parent.parent.parent.parent.parent.parent / "docs"
OUTPUT_PATH = DOCS_PATH / "docs-beta" / "docs" / (BASE_PATH + ".md")

NOTIFICATION_SERVICES = sorted(
    [
        NotificationService(
            name="email",
            label="Email",
            effect_description="an email",
            config_snippet={
                "email_addresses": [
                    "richard.hendricks@hooli.com",
                    "nelson.bighetti@hooli.com",
                ]
            },
            setup_prose="""No additional configuration is required to send emails from Dagster+.

All alert emails will be sent by `"no-reply@dagster.cloud"` or `"no-reply@<subdomain>.dagster.cloud"`. Alerts can be configured to be sent to any number of emails.""",
        ),
        NotificationService(
            name="slack",
            label="Slack",
            effect_description="a Slack message",
            config_snippet={
                "slack_workspace_name": "hooli",
                "slack_channel_name": "notifications",
            },
            setup_prose=""":::note
You will need sufficient permissions in Slack to add apps to your workspace.
:::
Navigate to **Deployment > Alerts** in the Dagster+ UI and click **Connect to Slack**. From there, you can complete the installation process.

When setting up an alert, you can choose a Slack channel to send those alerts to. Make sure to invite the `@Dagster+` bot to any channel that you'd like to receive an alert in.
""",
        ),
        NotificationService(
            name="pagerduty",
            label="PagerDuty",
            effect_description="a PagerDuty alert",
            config_snippet={"integration_key": "<pagerduty_integration_key>"},
            setup_prose=""":::note
You will need sufficient permissions in PagerDuty to add or edit services.
:::

In PagerDuty, you can either:

- [Create a new service](https://support.pagerduty.com/main/docs/services-and-integrations#create-a-service), and add Dagster+ as an integration, or
- [Edit an existing service](https://support.pagerduty.com/main/docs/services-and-integrations#edit-service-settings) to include Dagster+ as an integration

When configuring the integration, choose **Dagster+** as the integration type, and choose an integration name in the format `dagster-plus-{your_service_name}`.

After adding your new integration, you will be taken to a screen containing an **Integration Key**. This value will be required when configuring alerts in the UI (after selecting "PagerDuty" as your Notification Service) or using the CLI (in the `notification_service` configuration).
""",
        ),
        NotificationService(
            name="microsoft_teams",
            label="Microsoft Teams",
            effect_description="a Microsoft Teams webhook",
            config_snippet={"webhook_url": "https://yourdomain.webhook.office.com/..."},
            setup_prose="""Create an incoming webhook by following the [Microsoft Teams documentation](https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook?tabs=newteams%2Cdotnet).

This will provide you with a **webhook URL** which will be required when configuring alerts in the UI (after selecting "Microsoft Teams" as your Notification Service) or using the CLI (in the `notification_service` configuration).
""",
        ),
    ],
    key=lambda x: x.name,
)
ALERT_TYPES = [
    AlertType(
        condition_description="when a run fails",
        mdx_prose="""You can set up alerts to notify you when a run fails.

By default, these alerts will target all runs in the deployment, but they can be scoped to runs with a specific tag.""",
        ui_label="Run alert",
        ui_prose="5. Select **Job failure**.\n\nIf desired, add **tags** in the format `{key}:{value}` to filter the runs that will be considered.",
        alert_name="schedule-sensor-failure",
        event_types=["JOB_FAILURE"],
        config_snippet={"tags": {"important": "true"}},
    ),
    AlertType(
        condition_description="when a run is taking too long to complete",
        mdx_prose="""You can set up alerts to notify you whenever a run takes more than some threshold amount of time.

        By default, these alerts will target all runs in the deployment, but they can be scoped to runs with a specific tag.""",
        ui_label="Run alert",
        ui_prose="5. Select **Job running over** and how many hours to alert after.\n\nIf desired, add **tags** in the format `{key}:{value}` to filter the runs that will be considered.",
        alert_name="job-running-over-one-hour",
        event_types=["JOB_LONG_RUNNING"],
        config_snippet={
            "alert_targets": [
                {"long_running_job_threshold_target": {"threshold_seconds": 3600}}
            ],
            "tags": {"important": "true"},
        },
    ),
    AlertType(
        condition_description="when an asset fails to materialize",
        mdx_prose="""You can set up alerts to notify you when an asset materialization attempt fails.

By default, these alerts will target all assets in the deployment, but they can be scoped to a specific asset or group of assets.""",
        ui_label="Asset alert",
        ui_prose="5. Select **Failure** under the **Materializations** heading.\n\nIf desired, select a **target** from the dropdown menu to scope this alert to a specific asset or group.",
        alert_name="schedule-sensor-failure",
        event_types=["ASSET_MATERIALIZATION_FAILED"],
        config_snippet={
            "alert_targets": [
                {"asset_key_target": {"asset_key": ["s3", "report"]}},
                {
                    "asset_group_target": {
                        "asset_group": "transformed",
                        "location_name": "prod",
                        "repo_name": "__repository__",
                    }
                },
            ],
        },
    ),
    AlertType(
        condition_description="when an asset check fails",
        mdx_prose="""You can set up alerts to notify you when an asset check on an asset fails.

By default, these alerts will target all assets in the deployment, but they can be scoped to checks on a specific asset or group of assets.""",
        ui_label="Asset alert",
        ui_prose="5. Select **Failed (ERROR)** under the **Asset Checks** heading.\n\nIf desired, select a **target** from the dropdown menu to scope this alert to a specific asset or group.",
        alert_name="asset-check-failed",
        event_types=["ASSET_CHECK_SEVERITY_ERROR"],
        config_snippet={
            "alert_targets": [
                {"asset_key_target": {"asset_key": ["s3", "report"]}},
                {
                    "asset_group_target": {
                        "asset_group": "transformed",
                        "location_name": "prod",
                        "repo_name": "__repository__",
                    }
                },
            ],
        },
    ),
    AlertType(
        condition_description="when a schedule or sensor tick fails",
        mdx_prose="""You can set up alerts to fire when any schedule or sensor tick across your entire deployment fails.

Alerts are sent only when a schedule/sensor transitions from **success** to **failure**, so only the initial failure will trigger the alert.""",
        ui_label="Schedule/Sensor alert",
        alert_name="schedule-sensor-failure",
        event_types=["TICK_FAILURE"],
        config_snippet=None,
    ),
    AlertType(
        condition_description="when a code location fails to load",
        mdx_prose="You can set up alerts to fire when any code location fails to load due to an error.",
        ui_label="Code location error alert",
        alert_name="code-location-error",
        event_types=["CODE_LOCATION_ERROR"],
        config_snippet=None,
    ),
    AlertType(
        condition_description="when a Hybrid agent becomes unavailable",
        mdx_prose=""":::note
This is only available for [Hybrid](/todo) deployments.
:::

You can set up alerts to fire if your Hybrid agent hasn't sent a heartbeat in the last 5 minutes.""",
        ui_label="Code location error alert",
        alert_name="code-location-error",
        event_types=["AGENT_UNAVAILABLE"],
        config_snippet=None,
    ),
]


def _code_link(alert: AlertType, service: NotificationService) -> str:
    # creates a yaml code sample, writes it to the local directory, then returns a mdx link to it
    alert_name = f"{alert.alert_name}-{service.name}"
    yaml_block = yaml.dump(
        dict(
            alert_policies=dict(
                name=alert_name,
                event_types=alert.event_types,
                description=f"Sends {service.effect_description} {alert.condition_description}.",
                **(alert.config_snippet if alert.config_snippet else {}),
                notification_service=service.config_snippet,
            )
        ),
    )
    path = f"{alert_name}.yaml"
    with open(Path(__file__).parent / path, "w") as f:
        f.write(f"# alert_policies.yaml\n\n{yaml_block}")

    return f'<CodeExample filePath="{BASE_PATH}/{path}" language="yaml" />'


def _tab_item(value: str, label: str, inner: str, indent: int = 2) -> str:
    section = f"{' '*indent}<TabItem value='{value}' label='{label}'>\n"
    section += f"{' '*(indent+2)}{inner}\n"
    section += f"{' '*indent}</TabItem>\n"
    return section


def _generate_outputs() -> str:
    section = f"""---
title: Setting up alerts on Dagster+
sidebar_position: 30
sidebar_label: "Dagster+ Alerts"
---
[comment]: <> (This file is automatically generated by `{BASE_PATH}/generate_alerts_doc.py`)

Dagster+ allows you to configure alerts to automatically fire in response to a range of events. These alerts can be sent to a variety of different services, depending on your organization's needs.

These alerts can be configured in the Dagster+ UI, or using the `dagster-cloud` CLI tool.

<details>
<summary>Prerequisites</summary>
- **Organization**, **Admin**, or **Editor** permissions on Dagster+
</details>

"""
    # setup information
    section += "## Configuring a notification service\n\n"
    section += "To start, you'll need to configure a service to send alerts. Dagster+ current supports sending alerts through "
    for service in NOTIFICATION_SERVICES[:-1]:
        section += service.label if service.label != "Email" else "email"
        section += ", "
    section += f"and {NOTIFICATION_SERVICES[-1].label}.\n\n"

    section += '<Tabs groupId="notification_service">\n'
    for service in NOTIFICATION_SERVICES:
        section += _tab_item(service.name, service.label, service.setup_prose)
    section += "</Tabs>\n\n"

    # sepecific alert types
    for alert in ALERT_TYPES:
        section += f"## Alerting {alert.condition_description}\n{alert.mdx_prose}\n"
        section += '<Tabs groupId="ui_or_code">\n'

        ui_inner = f"""1. In the Dagster UI, click **Deployment**.
2. Click the **Alerts** tab.
3. Click **Add alert policy**.
4. Select **{alert.ui_label}** from the dropdown."""
        if alert.ui_prose:
            ui_inner += "\n\n" + alert.ui_prose + "\n"
        section += _tab_item(value="ui", label="In the UI", inner=ui_inner)

        code_options = """Execute the following command to sync the configured alert policy to your Dagster+ deployment.

  ```bash
  dagster-cloud deployment alert-policies sync -a /path/to/alert_policies.yaml
  ```
"""
        code_options += '  <Tabs groupId="notification_service">\n'
        for service in NOTIFICATION_SERVICES:
            code_options += _tab_item(
                service.name, service.label, _code_link(alert, service), indent=4
            )
        code_options += "  </Tabs>\n"

        section += _tab_item(value="code", label="In code", inner=code_options)
        section += "</Tabs>\n\n"

    return section


if __name__ == "__main__":
    output = _generate_outputs().strip()
    with open(str(OUTPUT_PATH), "w") as f:
        f.write(output)
