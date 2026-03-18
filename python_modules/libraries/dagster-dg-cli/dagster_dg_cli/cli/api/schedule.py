"""Schedule API commands following GitHub CLI patterns."""

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.formatters import format_schedule, format_schedules, format_ticks
from dagster_dg_cli.cli.api.shared import handle_api_errors
from dagster_dg_cli.cli.response_schema import dg_response_schema


@click.command(name="list", cls=DgClickCommand)
@click.option(
    "--status",
    type=click.Choice(["RUNNING", "STOPPED"]),
    help="Filter schedules by status",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_dg_cli.api_layer.schemas.schedule", cls="DgApiScheduleList")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def list_schedules_command(
    ctx: click.Context,
    status: str,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """List schedules in the deployment."""
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.schedule import DgApiScheduleApi

    api = DgApiScheduleApi(client)

    with handle_api_errors(ctx, output_json):
        schedules = api.list_schedules()

        if status:
            from dagster_dg_cli.api_layer.schemas.schedule import (
                DgApiScheduleList,
                DgApiScheduleStatus,
            )

            filtered_schedules = [
                schedule
                for schedule in schedules.items
                if schedule.status == DgApiScheduleStatus(status)
            ]
            schedules = DgApiScheduleList(items=filtered_schedules, total=len(filtered_schedules))

        output = format_schedules(schedules, as_json=output_json)
        click.echo(output)


@click.command(name="get", cls=DgClickCommand)
@click.argument("schedule_name", type=str)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_dg_cli.api_layer.schemas.schedule", cls="DgApiSchedule")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_schedule_command(
    ctx: click.Context,
    schedule_name: str,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Get specific schedule details."""
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.schedule import DgApiScheduleApi

    api = DgApiScheduleApi(client)

    with handle_api_errors(ctx, output_json):
        schedule = api.get_schedule_by_name(schedule_name=schedule_name)
        output = format_schedule(schedule, as_json=output_json)
        click.echo(output)


@click.command(name="get-ticks", cls=DgClickCommand)
@click.argument("schedule_name", type=str)
@click.option(
    "--status",
    "statuses",
    multiple=True,
    type=click.Choice(["STARTED", "SKIPPED", "SUCCESS", "FAILURE"], case_sensitive=False),
    help="Filter by tick status. Repeatable.",
)
@click.option("--limit", type=int, default=25, help="Maximum number of ticks to return")
@click.option("--cursor", type=str, help="Pagination cursor")
@click.option(
    "--before", "before_timestamp", type=float, help="Filter ticks before this Unix timestamp"
)
@click.option(
    "--after", "after_timestamp", type=float, help="Filter ticks after this Unix timestamp"
)
@click.option("--json", "output_json", is_flag=True, help="Output in JSON format")
@dg_response_schema(module="dagster_dg_cli.api_layer.schemas.tick", cls="DgApiTickList")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_schedule_ticks_command(
    ctx: click.Context,
    schedule_name: str,
    statuses: tuple[str, ...],
    limit: int,
    cursor: str | None,
    before_timestamp: float | None,
    after_timestamp: float | None,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Get tick history for a specific schedule."""
    from dagster_dg_cli.api_layer.api.tick import DgApiTickApi

    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    api = DgApiTickApi(client)

    with handle_api_errors(ctx, output_json):
        normalized_statuses = tuple(s.upper() for s in statuses)
        ticks = api.get_schedule_ticks(
            schedule_name=schedule_name,
            limit=limit,
            cursor=cursor,
            statuses=normalized_statuses,
            before_timestamp=before_timestamp,
            after_timestamp=after_timestamp,
        )
        output = format_ticks(ticks, name=schedule_name, as_json=output_json)
        click.echo(output)


@click.group(
    name="schedule",
    cls=DgClickGroup,
    commands={
        "list": list_schedules_command,
        "get": get_schedule_command,
        "get-ticks": get_schedule_ticks_command,
    },
)
def schedule_group():
    """Manage schedules in Dagster Plus."""
