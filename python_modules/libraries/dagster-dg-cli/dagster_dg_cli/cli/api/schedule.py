"""Schedule API commands following GitHub CLI patterns."""

import sys

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.formatters import format_schedule, format_schedules
from dagster_dg_cli.cli.api.shared import format_error_for_output


@click.command(name="list", cls=DgClickCommand, unlaunched=True)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def list_schedules_command(
    ctx: click.Context,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """List schedules."""
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.schedule import DgApiScheduleApi

    api = DgApiScheduleApi(client)

    try:
        schedules = api.list_schedules()
        output = format_schedules(schedules, as_json=output_json)
        click.echo(output)
    except Exception as e:
        error_output, exit_code = format_error_for_output(e, output_json)
        click.echo(error_output, err=True)
        sys.exit(exit_code)


@click.command(name="get", cls=DgClickCommand, unlaunched=True)
@click.argument("schedule_name", type=str)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
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

    try:
        schedule = api.get_schedule(schedule_name)
        output = format_schedule(schedule, as_json=output_json)
        click.echo(output)
    except Exception as e:
        error_output, exit_code = format_error_for_output(e, output_json)
        click.echo(error_output, err=True)
        sys.exit(exit_code)


@click.group(
    name="schedule",
    cls=DgClickGroup,
    unlaunched=True,
    commands={
        "list": list_schedules_command,
        "get": get_schedule_command,
    },
)
def schedule_group():
    """Manage schedules in Dagster Plus."""
