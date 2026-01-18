"""Schedule API commands following GitHub CLI patterns."""

import json
from typing import TYPE_CHECKING

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.formatters import _format_timestamp

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.schedule import DgApiSchedule, DgApiScheduleList


def format_schedules(schedules: "DgApiScheduleList", as_json: bool) -> str:
    """Format schedule list for output."""
    if as_json:
        schedules_dict = schedules.model_dump()
        for schedule in schedules_dict["items"]:
            schedule.pop("code_location_origin", None)
            schedule.pop("id", None)
        return json.dumps(schedules_dict, indent=2)

    lines = []
    for schedule in schedules.items:
        schedule_lines = [
            f"Name: {schedule.name}",
            f"Status: {schedule.status.value}",
            f"Cron Schedule: {schedule.cron_schedule}",
            f"Pipeline: {schedule.pipeline_name}",
            f"Description: {schedule.description or 'None'}",
        ]

        if schedule.execution_timezone:
            schedule_lines.append(f"Timezone: {schedule.execution_timezone}")

        if schedule.next_tick_timestamp:
            next_tick_str = _format_timestamp(schedule.next_tick_timestamp)
            schedule_lines.append(f"Next Tick: {next_tick_str}")

        schedule_lines.append("")  # Empty line between schedules
        lines.extend(schedule_lines)

    return "\n".join(lines).rstrip()  # Remove trailing empty line


def format_schedule(schedule: "DgApiSchedule", as_json: bool) -> str:
    """Format single schedule for output."""
    if as_json:
        schedule_dict = schedule.model_dump()
        schedule_dict.pop("code_location_origin", None)
        schedule_dict.pop("id", None)
        return json.dumps(schedule_dict, indent=2)

    lines = [
        f"Name: {schedule.name}",
        f"Status: {schedule.status.value}",
        f"Cron Schedule: {schedule.cron_schedule}",
        f"Pipeline: {schedule.pipeline_name}",
        f"Description: {schedule.description or 'None'}",
    ]

    if schedule.execution_timezone:
        lines.append(f"Timezone: {schedule.execution_timezone}")

    if schedule.next_tick_timestamp:
        next_tick_str = _format_timestamp(schedule.next_tick_timestamp)
        lines.append(f"Next Tick: {next_tick_str}")

    return "\n".join(lines)


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

    try:
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
    except Exception as e:
        if output_json:
            error_response = {"error": str(e)}
            click.echo(json.dumps(error_response), err=True)
            ctx.exit(1)
        else:
            raise click.ClickException(f"Failed to list schedules: {e}")


@click.command(name="get", cls=DgClickCommand)
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
        schedule = api.get_schedule_by_name(schedule_name=schedule_name)
        output = format_schedule(schedule, as_json=output_json)
        click.echo(output)
    except Exception as e:
        if output_json:
            error_response = {"error": str(e)}
            click.echo(json.dumps(error_response), err=True)
            ctx.exit(1)
        else:
            raise click.ClickException(f"Failed to get schedule: {e}")


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
