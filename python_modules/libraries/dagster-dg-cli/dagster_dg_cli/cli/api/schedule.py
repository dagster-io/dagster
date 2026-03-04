"""Schedule API commands following GitHub CLI patterns."""

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.formatters import format_schedule, format_schedules
from dagster_dg_cli.cli.api.shared import handle_api_errors
from dagster_dg_cli.cli.api.utils import dg_api_response_schema


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
@dg_api_response_schema(module="dagster_dg_cli.api_layer.schemas.schedule", cls="DgApiScheduleList")
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
@dg_api_response_schema(module="dagster_dg_cli.api_layer.schemas.schedule", cls="DgApiSchedule")
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


@click.group(
    name="schedule",
    cls=DgClickGroup,
    commands={
        "list": list_schedules_command,
        "get": get_schedule_command,
    },
)
def schedule_group():
    """Manage schedules in Dagster Plus."""
