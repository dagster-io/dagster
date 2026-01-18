"""Run events API commands following GitHub CLI patterns."""

import json

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

from dagster_dg_cli.api_layer.api.run_event import DgApiRunEventApi
from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client


def format_run_events_table(events, run_id: str) -> str:
    """Format run events as human-readable table."""
    if not events.items:
        return f"No events found for run {run_id}"

    lines = [f"Events for run {run_id}:", ""]

    # Table header
    header = f"{'TIMESTAMP':<20} {'TYPE':<20} {'STEP_KEY':<30} {'MESSAGE':<50}"
    separator = "-" * len(header)
    lines.extend([header, separator])

    # Table rows
    for event in events.items:
        timestamp = event.timestamp[:19]  # Truncate to YYYY-MM-DDTHH:MM:SS
        event_type = event.event_type
        step_key = event.step_key or ""
        message = event.message[:47] + "..." if len(event.message) > 50 else event.message

        row = f"{timestamp:<20} {event_type:<20} {step_key:<30} {message:<50}"
        lines.append(row)

    lines.extend(["", f"Total events: {events.total}"])
    return "\n".join(lines)


def format_run_events_json(events, run_id: str) -> str:
    """Format run events as JSON."""
    return json.dumps(
        {
            "run_id": run_id,
            "events": [
                {
                    "runId": event.run_id,
                    "message": event.message,
                    "timestamp": event.timestamp,
                    "level": event.level,
                    "stepKey": event.step_key,
                    "eventType": event.event_type,
                }
                for event in events.items
            ],
            "count": events.total,
        },
        indent=2,
    )


@click.command(name="get", cls=DgClickCommand)
@click.argument("run_id", type=str)
@click.option(
    "--type",
    "event_type",
    help="Filter by event type (comma-separated)",
)
@click.option(
    "--step",
    "step_key",
    help="Filter by step key (partial matching)",
)
@click.option(
    "--limit",
    type=int,
    default=100,
    help="Maximum number of events to return",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_run_events_command(
    ctx: click.Context,
    run_id: str,
    event_type: str,
    step_key: str,
    limit: int,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
) -> None:
    """Get run events with filtering options."""
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config)
    api = DgApiRunEventApi(client)

    try:
        events = api.get_events(
            run_id=run_id, event_type=event_type, step_key=step_key, limit=limit
        )

        if output_json:
            output = format_run_events_json(events, run_id)
        else:
            output = format_run_events_table(events, run_id)

        click.echo(output)
    except Exception as e:
        if output_json:
            error_response = {"error": str(e)}
            click.echo(json.dumps(error_response), err=True)
        else:
            click.echo(f"Error querying Dagster Plus API: {e}", err=True)


@click.group(
    name="run-events",
    cls=DgClickGroup,
    commands={
        "get": get_run_events_command,
    },
)
def run_events_group():
    """Manage run events in Dagster Plus."""
