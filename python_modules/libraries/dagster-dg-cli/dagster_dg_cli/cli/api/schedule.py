"""Schedule API commands following GitHub CLI patterns."""

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_rest_resources.schemas.enums import DgApiInstigationTickStatus
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
@dg_response_schema(module="dagster_rest_resources.schemas.schedule", cls="DgApiScheduleList")
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
    """List schedules in the deployment.

    Example::

        $ dg api schedule list
        NAME                       STATUS   CRON           PIPELINE
        daily_customer_ingest      RUNNING  0 6 * * *      ingest_customers
        hourly_event_aggregation   RUNNING  0 * * * *      aggregate_events
        weekly_model_retrain       STOPPED  0 9 * * MON    retrain_recommendation_model
    """
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_rest_resources.api.schedule import DgApiScheduleApi

    api = DgApiScheduleApi(_client=client)

    with handle_api_errors(ctx, output_json):
        schedules = api.list_schedules()

        if status:
            from dagster_rest_resources.schemas.enums import DgApiInstigationStatus
            from dagster_rest_resources.schemas.schedule import DgApiScheduleList

            filtered_schedules = [
                schedule
                for schedule in schedules.items
                if schedule.status == DgApiInstigationStatus(status)
            ]
            schedules = DgApiScheduleList(items=filtered_schedules)

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
@dg_response_schema(module="dagster_rest_resources.schemas.schedule", cls="DgApiSchedule")
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
    """Get specific schedule details.

    Example::

        $ dg api schedule get daily_customer_ingest
        Name:          daily_customer_ingest
        Status:        RUNNING
        Cron Schedule: 0 6 * * *
        Pipeline:      ingest_customers
        Description:   Daily customer ingest at 06:00 UTC
        Timezone:      UTC
        Next Tick:     2026-05-07 06:00:00 UTC
    """
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_rest_resources.api.schedule import DgApiScheduleApi

    api = DgApiScheduleApi(_client=client)

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
def get_schedule_ticks_command(
    ctx: click.Context,
    schedule_name: str,
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
    """Get tick history for a specific schedule.

    Example::

        $ dg api schedule get-ticks daily_customer_ingest --limit 3
        TIMESTAMP                STATUS    RUN IDS                               SKIP REASON
        2026-05-06 06:00:00 UTC  SUCCESS   5b3c8a91-2e4f-4d7b-9c6a-1f8d3e5b2c4a
        2026-05-05 06:00:00 UTC  SUCCESS   2a1f7b3c-9d8e-4c5b-8a6d-3f1e2b9c4d7a
        2026-05-04 06:00:00 UTC  FAILURE   8c4d2e7f-1a9b-4e3d-7c5b-9f2a1d8e3b6c

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
        ticks = api.get_schedule_ticks(
            schedule_name=schedule_name,
            limit=limit,
            cursor=cursor,
            statuses=list(statuses) if statuses else None,
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
