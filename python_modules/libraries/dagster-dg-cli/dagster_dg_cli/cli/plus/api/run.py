"""Run API commands following GitHub CLI patterns."""

import json
from typing import Any, Optional

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.cli.plus.api.formatters import format_run_events
from dagster_dg_cli.utils.plus.gql import RUN_EVENTS_QUERY
from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient


def _get_config_or_error() -> DagsterPlusCliConfig:
    if not DagsterPlusCliConfig.exists():
        raise click.UsageError(
            "`dg plus` commands require authentication with Dagster Plus. Run `dg plus login` to authenticate."
        )
    return DagsterPlusCliConfig.get()


def _filter_events_by_type(
    events: list[dict[str, Any]], event_type: Optional[str]
) -> list[dict[str, Any]]:
    """Filter events by event type if specified."""
    if not event_type:
        return events

    # Split comma-separated types and normalize
    types = [t.strip().upper() for t in event_type.split(",")]

    filtered = []
    for event in events:
        event_type_val = event.get("eventType")
        if event_type_val and event_type_val.upper() in types:
            filtered.append(event)

    return filtered


def _filter_events_by_step(
    events: list[dict[str, Any]], step_key: Optional[str]
) -> list[dict[str, Any]]:
    """Filter events by step key if specified."""
    if not step_key:
        return events

    filtered = []
    for event in events:
        event_step = event.get("stepKey", "")
        if event_step and step_key.lower() in event_step.lower():
            filtered.append(event)

    return filtered


@click.command(name="events", cls=DgClickCommand, unlaunched=True)
@click.argument("run_id", required=True)
@click.option(
    "--type",
    "event_type",
    help="Filter by event type (STEP_SUCCESS, STEP_FAILURE, MATERIALIZATION, etc.)",
)
@click.option(
    "--step",
    "step_key",
    help="Filter by step key (supports partial matching)",
)
@click.option(
    "--limit",
    type=int,
    default=100,
    help="Maximum number of events to return (default: 100)",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@cli_telemetry_wrapper
def events_run_command(
    run_id: str, event_type: Optional[str], step_key: Optional[str], limit: int, output_json: bool
) -> None:
    """Get events for a specific run with filtering options."""
    config = _get_config_or_error()

    try:
        client = DagsterPlusGraphQLClient.from_config(config)
        result = client.execute(RUN_EVENTS_QUERY, {"runId": run_id, "limit": limit})

        # Handle case where result is None (empty response)
        if result is None:
            if output_json:
                click.echo(
                    json.dumps({"error": f"No response from GraphQL API for run {run_id}"}),
                    err=True,
                )
            else:
                click.echo(f"No response from GraphQL API for run {run_id}", err=True)
            raise click.ClickException(
                f"Failed to get events for run {run_id}: No response from API"
            )

        # Handle GraphQL response structure
        logs_result = result.get("logsForRun")
        if not logs_result:
            if output_json:
                click.echo(json.dumps({"error": f"No events found for run {run_id}"}), err=True)
            else:
                click.echo(f"No events found for run {run_id}", err=True)
            raise click.ClickException(f"Failed to get events for run {run_id}")

        # Check for error types in GraphQL response
        if logs_result.get("__typename") == "PythonError":
            error_msg = logs_result.get("message", "Unknown error")
            if output_json:
                click.echo(json.dumps({"error": error_msg}), err=True)
            else:
                click.echo(f"Error: {error_msg}", err=True)
            raise click.ClickException(f"Failed to get events for run {run_id}: {error_msg}")

        # Extract events from the connection
        events = []
        if logs_result.get("events"):
            events = logs_result["events"]

        # Apply filtering
        if event_type:
            events = _filter_events_by_type(events, event_type)

        if step_key:
            events = _filter_events_by_step(events, step_key)

        # Format and output
        output = format_run_events(events, as_json=output_json, run_id=run_id)
        click.echo(output)

    except Exception as e:
        if output_json:
            error_response = {"error": str(e), "run_id": run_id}
            click.echo(json.dumps(error_response), err=True)
        else:
            click.echo(f"Error querying Dagster Plus API: {e}", err=True)
        raise click.ClickException(f"Failed to get events for run {run_id}: {e}")


@click.group(
    name="run",
    cls=DgClickGroup,
    unlaunched=True,
    commands={
        "events": events_run_command,
    },
)
def run_group():
    """Manage runs in Dagster Plus."""
