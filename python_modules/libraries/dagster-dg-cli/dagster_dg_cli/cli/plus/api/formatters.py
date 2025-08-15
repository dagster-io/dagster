"""Output formatters for CLI display."""

import json
from typing import Any

from dagster_dg_cli.dagster_plus_api.schemas.deployment import DeploymentList


def format_deployments(deployments: DeploymentList, as_json: bool) -> str:
    """Format deployment list for output."""
    if as_json:
        return deployments.model_dump_json(indent=2)

    lines = []
    for deployment in deployments.items:
        lines.extend(
            [
                f"Name: {deployment.name}",
                f"ID: {deployment.id}",
                f"Type: {deployment.type.value}",
                "",  # Empty line between deployments
            ]
        )

    return "\n".join(lines).rstrip()  # Remove trailing empty line


def format_run_events(events: list[dict[str, Any]], as_json: bool, run_id: str) -> str:
    """Format run events for output."""
    if as_json:
        return json.dumps({"run_id": run_id, "events": events, "count": len(events)}, indent=2)

    if not events:
        return f"No events found for run {run_id}"

    # Human-readable table format
    lines = [
        f"Events for run {run_id}:",
        "",
        f"{'TIMESTAMP':<20} {'TYPE':<20} {'STEP_KEY':<30} {'MESSAGE'[:50]:<50}",
        f"{'-' * 20} {'-' * 20} {'-' * 30} {'-' * 50}",
    ]

    for event in events:
        # Handle None values safely
        timestamp = (event.get("timestamp") or "")[:19]  # Truncate timestamp
        event_type = (event.get("eventType") or "")[:20]  # Truncate type
        step_key = (event.get("stepKey") or "")[:30]  # Truncate step key
        message = (event.get("message") or "")[:50]  # Truncate message

        lines.append(f"{timestamp:<20} {event_type:<20} {step_key:<30} {message:<50}")

    lines.extend(["", f"Total events: {len(events)}"])

    return "\n".join(lines)
