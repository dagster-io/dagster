# This script is used to generate docs snippets referenced in `example-config.md`. It creates and formats the cross-product
# of all alert types and notification services. After adding a new alert type or service, just run
# `python generate_alerts_config_code_snippets.py` and the corresponding YAML files will be created or updated.
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, NamedTuple, Optional

import yaml


class NotificationService(NamedTuple):
    name: str
    label: str
    effect_description: str
    config_snippet: Mapping[str, Any]


class AlertType(NamedTuple):
    condition_description: str
    alert_name: str
    event_types: Sequence[str]
    config_snippet: Optional[Mapping[str, Any]]


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
        ),
        NotificationService(
            name="slack",
            label="Slack",
            effect_description="a Slack message",
            config_snippet={
                "slack_workspace_name": "hooli",
                "slack_channel_name": "notifications",
            },
        ),
        NotificationService(
            name="pagerduty",
            label="PagerDuty",
            effect_description="a PagerDuty alert",
            config_snippet={"integration_key": "<pagerduty_integration_key>"},
        ),
        NotificationService(
            name="microsoft_teams",
            label="Microsoft Teams",
            effect_description="a Microsoft Teams webhook",
            config_snippet={"webhook_url": "https://yourdomain.webhook.office.com/..."},
        ),
    ],
    key=lambda x: x.name,
)
ALERT_TYPES = [
    AlertType(
        condition_description="when a run fails",
        alert_name="run-alert-failure",
        event_types=["JOB_FAILURE"],
        config_snippet={"tags": {"important": "true"}},
    ),
    AlertType(
        condition_description="when a run is taking too long to complete",
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
        alert_name="asset-materialization-failure-alert",
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
        alert_name="schedule-sensor-failure",
        event_types=["TICK_FAILURE"],
        config_snippet=None,
    ),
    AlertType(
        condition_description="when a code location fails to load",
        alert_name="code-location-error",
        event_types=["CODE_LOCATION_ERROR"],
        config_snippet=None,
    ),
    AlertType(
        condition_description="when a Hybrid agent hasn't sent a heartbeat in the last 5 minutes",
        alert_name="agent-unavailable-alert",
        event_types=["AGENT_UNAVAILABLE"],
        config_snippet=None,
    ),
    AlertType(
        condition_description="when an asset has exceeded a credit usage threshold",
        alert_name="insights-credit-alert",
        event_types=["INSIGHTS_CONSUMPTION_EXCEEDED"],
        config_snippet={
            "alert_targets": [
                {
                    "insights_asset_threshold_target": {
                        "metric_name": "__dagster_dagster_credits",
                        "selection_period_days": 7,
                        "threshold": 50,
                        "operator": "GREATER_THAN",
                        "asset_key": ["s3", "report"],
                    }
                },
            ],
        },
    ),
]


def _make_yaml_code_snippet(alert: AlertType, service: NotificationService) -> None:
    # creates a yaml code sample and writes it to the local directory
    alert_name = f"{alert.alert_name}-{service.name}"
    yaml_block = yaml.dump(
        dict(
            alert_policies=dict(
                name=alert_name,
                event_types=alert.event_types,
                description=f"Sends {service.effect_description} {alert.condition_description}.",
                **(alert.config_snippet if alert.config_snippet else {}),
                notification_service={service.name: service.config_snippet},
            )
        ),
    )
    path = f"{alert_name}.yaml"
    with open(Path(__file__).parent / path, "w") as f:
        f.write(f"# alert_policies.yaml\n\n{yaml_block}")


if __name__ == "__main__":
    for alert in ALERT_TYPES:
        for service in NOTIFICATION_SERVICES:
            _make_yaml_code_snippet(alert, service)
