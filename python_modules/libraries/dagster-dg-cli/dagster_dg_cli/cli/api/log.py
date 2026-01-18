"""Log API commands following GitHub CLI patterns."""

import datetime
import json

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

from dagster_dg_cli.api_layer.api.run_event import DgApiRunEventApi
from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client


def format_logs_table(events, run_id: str) -> str:
    """Format logs as human-readable table."""
    if not events.items:
        return f"No logs found for run {run_id}"

    lines = [f"Logs for run {run_id}:", ""]

    # Table header
    header = f"{'TIMESTAMP':<20} {'LEVEL':<8} {'STEP_KEY':<25} {'MESSAGE'}"
    separator = "-" * 80
    lines.extend([header, separator])

    # Table rows
    for event in events.items:
        # Convert Unix timestamp to readable format
        timestamp_ms = int(event.timestamp)
        dt = datetime.datetime.fromtimestamp(timestamp_ms / 1000.0)
        timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")

        level = event.level.value
        step_key = (event.step_key or "")[:24]  # Truncate long step keys
        message = event.message

        row = f"{timestamp_str:<20} {level:<8} {step_key:<25} {message}"
        lines.append(row)

        # Add stack trace for error events
        if event.error and event.error.stack:
            lines.append("")
            lines.append("Stack Trace:")
            # Format the stack trace with indentation
            stack_trace = event.error.get_stack_trace_string()
            for stack_line in stack_trace.split("\n"):
                if stack_line.strip():
                    lines.append(f"  {stack_line}")
            lines.append("")

    lines.extend(["", f"Total log entries: {events.total}"])
    if events.has_more:
        lines.append("Note: More logs available (use --limit to increase or --cursor to paginate)")

    return "\n".join(lines)


def format_logs_json(events, run_id: str) -> str:
    """Format logs as JSON."""

    def error_to_dict(error_info):
        """Convert ErrorInfo to dictionary recursively."""
        if not error_info:
            return None
        return {
            "message": error_info.message,
            "className": error_info.className,
            "stack": error_info.stack,  # Keep as list for JSON
            "stackTrace": error_info.get_stack_trace_string(),  # Also provide as string
            "cause": error_to_dict(error_info.cause) if error_info.cause else None,
        }

    return json.dumps(
        {
            "run_id": run_id,
            "logs": [
                {
                    "runId": event.run_id,
                    "message": event.message,
                    "timestamp": event.timestamp,
                    "level": event.level,
                    "stepKey": event.step_key,
                    "eventType": event.event_type,
                    "error": error_to_dict(event.error) if event.error else None,
                }
                for event in events.items
            ],
            "count": events.total,
            "cursor": events.cursor,
            "hasMore": events.has_more,
        },
        indent=2,
    )


@click.command(name="get", cls=DgClickCommand)
@click.argument("run_id", type=str)
@click.option(
    "--level",
    "log_level",
    help="Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
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
    help="Maximum number of log entries to return",
)
@click.option(
    "--cursor",
    "after_cursor",
    help="Pagination cursor for retrieving more logs",
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
def get_logs_command(
    ctx: click.Context,
    run_id: str,
    log_level: str,
    step_key: str,
    limit: int,
    after_cursor: str,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Get logs for a specific run ID."""
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    api = DgApiRunEventApi(client)

    try:
        # Use log level as event type filter if provided
        event_type = None
        if log_level:
            # Convert log level to event types that match that level
            # For now, we'll pass the level directly and let the filtering happen
            event_type = log_level.upper()

        logs = api.get_events(
            run_id=run_id,
            event_type=event_type,
            step_key=step_key,
            limit=limit,
            after_cursor=after_cursor,
        )

        if output_json:
            output = format_logs_json(logs, run_id)
        else:
            output = format_logs_table(logs, run_id)

        click.echo(output)
    except Exception as e:
        if output_json:
            error_response = {"error": str(e)}
            click.echo(json.dumps(error_response), err=True)
        else:
            click.echo(f"Error querying Dagster Plus API: {e}", err=True)
        raise click.ClickException(f"Failed to get logs for run {run_id}: {e}")


@click.group(
    name="log",
    cls=DgClickGroup,
    commands={
        "get": get_logs_command,
    },
)
def log_group():
    """Retrieve logs from Dagster Plus runs."""
