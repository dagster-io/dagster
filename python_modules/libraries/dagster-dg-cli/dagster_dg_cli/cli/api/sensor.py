"""Sensor API commands following GitHub CLI patterns."""

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.formatters import format_sensor, format_sensors, format_ticks
from dagster_dg_cli.cli.api.shared import handle_api_errors
from dagster_dg_cli.cli.response_schema import dg_response_schema


@click.command(name="list", cls=DgClickCommand)
@click.option(
    "--status",
    type=click.Choice(["RUNNING", "STOPPED", "PAUSED"]),
    help="Filter sensors by status",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_dg_cli.api_layer.schemas.sensor", cls="DgApiSensorList")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def list_sensors_command(
    ctx: click.Context,
    status: str,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """List sensors in the deployment."""
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.sensor import DgApiSensorApi

    api = DgApiSensorApi(client)

    with handle_api_errors(ctx, output_json):
        sensors = api.list_sensors()

        if status:
            from dagster_dg_cli.api_layer.schemas.sensor import DgApiSensorList, DgApiSensorStatus

            filtered_sensors = [
                sensor for sensor in sensors.items if sensor.status == DgApiSensorStatus(status)
            ]
            sensors = DgApiSensorList(items=filtered_sensors, total=len(filtered_sensors))

        output = format_sensors(sensors, as_json=output_json)
        click.echo(output)


@click.command(name="get", cls=DgClickCommand)
@click.argument("sensor_name", type=str)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_dg_cli.api_layer.schemas.sensor", cls="DgApiSensor")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_sensor_command(
    ctx: click.Context,
    sensor_name: str,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Get specific sensor details."""
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.sensor import DgApiSensorApi

    api = DgApiSensorApi(client)

    with handle_api_errors(ctx, output_json):
        sensor = api.get_sensor_by_name(sensor_name=sensor_name)
        output = format_sensor(sensor, as_json=output_json)
        click.echo(output)


@click.command(name="get-ticks", cls=DgClickCommand)
@click.argument("sensor_name", type=str)
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
def get_sensor_ticks_command(
    ctx: click.Context,
    sensor_name: str,
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
    """Get tick history for a specific sensor."""
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
        ticks = api.get_sensor_ticks(
            sensor_name=sensor_name,
            limit=limit,
            cursor=cursor,
            statuses=normalized_statuses,
            before_timestamp=before_timestamp,
            after_timestamp=after_timestamp,
        )
        output = format_ticks(ticks, name=sensor_name, as_json=output_json)
        click.echo(output)


@click.group(
    name="sensor",
    cls=DgClickGroup,
    commands={
        "list": list_sensors_command,
        "get": get_sensor_command,
        "get-ticks": get_sensor_ticks_command,
    },
)
def sensor_group():
    """Manage sensors in Dagster Plus."""
