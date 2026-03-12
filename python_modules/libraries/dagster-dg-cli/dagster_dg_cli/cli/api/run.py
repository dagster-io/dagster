"""Run API commands following GitHub CLI patterns."""

from typing import Final

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

from dagster_dg_cli.api_layer.api.run_event import DgApiRunEventApi
from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.formatters import (
    format_logs_json,
    format_logs_table,
    format_run,
    format_runs_list,
)
from dagster_dg_cli.cli.api.shared import handle_api_errors
from dagster_dg_cli.cli.response_schema import dg_response_schema

DG_API_MAX_RUN_LIMIT: Final = 1000


@click.command(name="list", cls=DgClickCommand)
@click.option(
    "--limit",
    type=click.IntRange(1, DG_API_MAX_RUN_LIMIT),
    default=50,
    help=f"Number of runs to return (default: 50, max: {DG_API_MAX_RUN_LIMIT})",
)
@click.option(
    "--cursor",
    type=str,
    help="Cursor for pagination (run ID)",
)
@click.option(
    "--status",
    "statuses",
    multiple=True,
    type=click.Choice(
        ["QUEUED", "STARTING", "STARTED", "SUCCESS", "FAILURE", "CANCELING", "CANCELED"],
        case_sensitive=False,
    ),
    help="Filter by run status. Repeatable.",
)
@click.option(
    "--job",
    "job_name",
    type=str,
    help="Filter by job name",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_dg_cli.api_layer.schemas.run", cls="DgApiRunList")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def list_runs_command(
    ctx: click.Context,
    limit: int,
    cursor: str,
    statuses: tuple[str, ...],
    job_name: str | None,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """List runs with optional filtering and pagination."""
    from dagster_dg_cli.api_layer.api.run import DgApiRunApi

    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    api = DgApiRunApi(client)

    with handle_api_errors(ctx, output_json):
        # Normalize statuses to uppercase
        normalized_statuses = tuple(s.upper() for s in statuses)
        runs = api.list_runs(
            limit=limit,
            cursor=cursor,
            statuses=normalized_statuses,
            job_name=job_name,
        )
        output = format_runs_list(runs, as_json=output_json)
        click.echo(output)


@click.command(name="get", cls=DgClickCommand)
@click.argument("run_id", type=str)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_dg_cli.api_layer.schemas.run", cls="DgApiRun")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_run_command(
    ctx: click.Context,
    run_id: str,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Get run metadata by ID."""
    from dagster_dg_cli.api_layer.api.run import DgApiRunApi

    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    api = DgApiRunApi(client)

    with handle_api_errors(ctx, output_json):
        run = api.get_run(run_id)
        output = format_run(run, as_json=output_json)
        click.echo(output)


@click.command(name="get-events", cls=DgClickCommand)
@click.argument("run_id", type=str)
@click.option(
    "--level",
    "levels",
    multiple=True,
    help="Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Repeatable.",
)
@click.option(
    "--event-type",
    "event_types",
    multiple=True,
    help="Filter by event type (e.g. STEP_FAILURE, RUN_START). Repeatable.",
)
@click.option(
    "--step",
    "step_keys",
    multiple=True,
    help="Filter by step key (partial matching). Repeatable.",
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
@dg_response_schema(module="dagster_dg_cli.api_layer.schemas.run_event", cls="RunEventList")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_events_run_command(
    ctx: click.Context,
    run_id: str,
    levels: tuple[str, ...],
    event_types: tuple[str, ...],
    step_keys: tuple[str, ...],
    limit: int,
    after_cursor: str,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Get execution log events for a specific run ID."""
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    api = DgApiRunEventApi(client)

    with handle_api_errors(ctx, output_json):
        logs = api.get_events(
            run_id=run_id,
            event_types=event_types,
            step_keys=step_keys,
            levels=levels,
            limit=limit,
            after_cursor=after_cursor,
        )

        if output_json:
            output = format_logs_json(logs)
        else:
            output = format_logs_table(logs, run_id)

        click.echo(output)


@click.group(
    name="run",
    cls=DgClickGroup,
    commands={
        "list": list_runs_command,
        "get": get_run_command,
        "get-events": get_events_run_command,
    },
)
def run_group():
    """Manage runs in Dagster Plus."""
