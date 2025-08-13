"""Run API commands following GitHub CLI patterns."""

import json
from typing import Optional

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.cli.api.formatters import format_run_events
from dagster_dg_cli.dagster_plus_api.api.runs import DgApiRunApi


def _get_config_or_error() -> DagsterPlusCliConfig:
    if not DagsterPlusCliConfig.exists():
        raise click.UsageError(
            "`dg plus` commands require authentication with Dagster Plus. Run `dg plus login` to authenticate."
        )
    return DagsterPlusCliConfig.get()


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
        run_api = DgApiRunApi(config)
        result = run_api.list_run_events(
            run_id=run_id, limit=limit, event_type=event_type, step_key=step_key
        )

        # Convert Pydantic models back to dict format for the formatter
        events = []
        for event in result.items:
            events.append(
                {
                    "runId": event.run_id,
                    "message": event.message,
                    "timestamp": event.timestamp,
                    "level": event.level.value,
                    "stepKey": event.step_key,
                    "eventType": event.event_type,
                }
            )

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
