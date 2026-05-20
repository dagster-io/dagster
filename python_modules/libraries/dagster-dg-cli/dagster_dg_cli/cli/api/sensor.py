"""Sensor API commands following GitHub CLI patterns."""

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_rest_resources.schemas.enums import DgApiInstigationTickStatus
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.formatters import format_sensor, format_sensors, format_ticks
from dagster_dg_cli.cli.api.shared import handle_api_errors
from dagster_dg_cli.cli.response_schema import dg_response_schema


@click.command(name="list", cls=DgClickCommand)
@click.option(
    "--status",
    type=click.Choice(["RUNNING", "STOPPED"]),
    help="Filter sensors by status",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_rest_resources.schemas.sensor", cls="DgApiSensorList")
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
    """List sensors in the deployment.

    Example::

        $ dg api sensor list
        NAME                         STATUS   TYPE
        new_file_sensor              RUNNING  STANDARD
        slack_alert_sensor           RUNNING  RUN_STATUS
        retrain_trigger_sensor       STOPPED  ASSET
    """
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_rest_resources.api.sensor import DgApiSensorApi

    api = DgApiSensorApi(_client=client)

    with handle_api_errors(ctx, output_json):
        sensors = api.list_sensors()

        if status:
            from dagster_rest_resources.schemas.enums import DgApiInstigationStatus
            from dagster_rest_resources.schemas.sensor import DgApiSensorList

            filtered_sensors = [
                sensor
                for sensor in sensors.items
                if sensor.status == DgApiInstigationStatus(status)
            ]
            sensors = DgApiSensorList(items=filtered_sensors)

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
@dg_response_schema(module="dagster_rest_resources.schemas.sensor", cls="DgApiSensor")
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
    """Get specific sensor details.

    Example::

        $ dg api sensor get new_file_sensor
        Name:        new_file_sensor
        Status:      RUNNING
        Type:        STANDARD
        Description: Triggers ingest_customers when a new file lands in S3
        Next Tick:   2026-05-06 18:43:00 UTC
    """
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_rest_resources.api.sensor import DgApiSensorApi

    api = DgApiSensorApi(_client=client)

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
    type=click.Choice([e.value for e in DgApiInstigationTickStatus], case_sensitive=False),
    callback=lambda ctx, param, values: tuple(
        DgApiInstigationTickStatus(v.upper()) for v in values
    ),
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
@dg_response_schema(module="dagster_rest_resources.schemas.tick", cls="DgApiTickList")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_sensor_ticks_command(
    ctx: click.Context,
    sensor_name: str,
    statuses: tuple[DgApiInstigationTickStatus, ...],
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
    """Get tick history for a specific sensor.

    Example::

        $ dg api sensor get-ticks new_file_sensor --limit 3
        TIMESTAMP                STATUS    RUN IDS                               SKIP REASON
        2026-05-06 18:42:00 UTC  SUCCESS   5b3c8a91-2e4f-4d7b-9c6a-1f8d3e5b2c4a
        2026-05-06 18:41:30 UTC  SKIPPED   -                                     No new files in s3://incoming/customers/
        2026-05-06 18:41:00 UTC  SKIPPED   -                                     No new files in s3://incoming/customers/

        Total ticks: 3
    """
    from dagster_rest_resources.api.tick import DgApiTickApi

    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    api = DgApiTickApi(_client=client)

    with handle_api_errors(ctx, output_json):
        ticks = api.get_sensor_ticks(
            sensor_name=sensor_name,
            limit=limit,
            cursor=cursor,
            statuses=list(statuses) if statuses else None,
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
