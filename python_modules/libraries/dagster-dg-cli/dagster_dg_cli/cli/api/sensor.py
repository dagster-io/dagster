"""Sensor API commands following GitHub CLI patterns."""

import datetime
import json
from typing import TYPE_CHECKING

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.sensor import DgApiSensor, DgApiSensorList


def format_sensors(sensors: "DgApiSensorList", as_json: bool) -> str:
    """Format sensor list for output."""
    if as_json:
        # For JSON output, remove repository_origin to hide repository concepts
        sensors_dict = sensors.model_dump()
        for sensor in sensors_dict["items"]:
            sensor.pop("repository_origin", None)
        return json.dumps(sensors_dict, indent=2)

    lines = []
    for sensor in sensors.items:
        sensor_lines = [
            f"Name: {sensor.name}",
            f"ID: {sensor.id}",
            f"Status: {sensor.status.value}",
            f"Type: {sensor.sensor_type.value}",
            f"Description: {sensor.description or 'None'}",
        ]

        # Hide repository information from end users
        # if sensor.repository_origin:
        #     sensor_lines.append(f"Repository: {sensor.repository_origin}")

        if sensor.next_tick_timestamp:
            try:
                dt = datetime.datetime.fromtimestamp(sensor.next_tick_timestamp)
                next_tick_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, OSError):
                next_tick_str = f"Invalid timestamp: {sensor.next_tick_timestamp}"
            sensor_lines.append(f"Next Tick: {next_tick_str}")

        sensor_lines.append("")  # Empty line between sensors
        lines.extend(sensor_lines)

    return "\n".join(lines).rstrip()  # Remove trailing empty line


def format_sensor(sensor: "DgApiSensor", as_json: bool) -> str:
    """Format single sensor for output."""
    if as_json:
        # For JSON output, remove repository_origin to hide repository concepts
        sensor_dict = sensor.model_dump()
        sensor_dict.pop("repository_origin", None)
        return json.dumps(sensor_dict, indent=2)

    lines = [
        f"Name: {sensor.name}",
        f"ID: {sensor.id}",
        f"Status: {sensor.status.value}",
        f"Type: {sensor.sensor_type.value}",
        f"Description: {sensor.description or 'None'}",
    ]

    # Hide repository information from end users
    # if sensor.repository_origin:
    #     lines.append(f"Repository: {sensor.repository_origin}")

    if sensor.next_tick_timestamp:
        try:
            dt = datetime.datetime.fromtimestamp(sensor.next_tick_timestamp)
            next_tick_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, OSError):
            next_tick_str = f"Invalid timestamp: {sensor.next_tick_timestamp}"
        lines.append(f"Next Tick: {next_tick_str}")

    return "\n".join(lines)


@click.command(name="list", cls=DgClickCommand, unlaunched=True)
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

    try:
        # Always list all sensors (no repository filtering for end users)
        sensors = api.list_sensors()

        # Apply status filter if specified
        if status:
            from dagster_dg_cli.api_layer.schemas.sensor import DgApiSensorList, DgApiSensorStatus

            filtered_sensors = [
                sensor for sensor in sensors.items if sensor.status == DgApiSensorStatus(status)
            ]
            sensors = DgApiSensorList(items=filtered_sensors, total=len(filtered_sensors))

        output = format_sensors(sensors, as_json=output_json)
        click.echo(output)
    except Exception as e:
        if output_json:
            error_response = {"error": str(e)}
            click.echo(json.dumps(error_response), err=True)
        else:
            click.echo(f"Error querying Dagster Plus API: {e}", err=True)
        raise click.ClickException(f"Failed to list sensors: {e}")


@click.command(name="get", cls=DgClickCommand, unlaunched=True)
@click.argument("sensor_name", type=str)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
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

    try:
        sensor = api.get_sensor_by_name(sensor_name=sensor_name)
        output = format_sensor(sensor, as_json=output_json)
        click.echo(output)
    except Exception as e:
        if output_json:
            error_response = {"error": str(e)}
            click.echo(json.dumps(error_response), err=True)
        else:
            click.echo(f"Error querying Dagster Plus API: {e}", err=True)
        raise click.ClickException(f"Failed to get sensor: {e}")


@click.group(
    name="sensor",
    cls=DgClickGroup,
    unlaunched=True,
    commands={
        "list": list_sensors_command,
        "get": get_sensor_command,
    },
)
def sensor_group():
    """Manage sensors in Dagster Plus."""
