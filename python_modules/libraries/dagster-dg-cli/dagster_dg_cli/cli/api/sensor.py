"""Sensor API commands following GitHub CLI patterns."""

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.formatters import format_sensor, format_sensors
from dagster_dg_cli.cli.api.shared import handle_api_errors
from dagster_dg_cli.cli.api.utils import dg_api_response_schema


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
@dg_api_response_schema(module="dagster_dg_cli.api_layer.schemas.sensor", cls="DgApiSensorList")
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
@dg_api_response_schema(module="dagster_dg_cli.api_layer.schemas.sensor", cls="DgApiSensor")
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


@click.group(
    name="sensor",
    cls=DgClickGroup,
    commands={
        "list": list_sensors_command,
        "get": get_sensor_command,
    },
)
def sensor_group():
    """Manage sensors in Dagster Plus."""
