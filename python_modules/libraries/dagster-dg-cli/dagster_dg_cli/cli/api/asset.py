"""Asset API commands following GitHub CLI patterns."""

from typing import Final, Literal

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.formatters import (
    format_asset,
    format_asset_evaluations,
    format_asset_events,
    format_asset_health,
    format_assets,
    format_partition_status,
)
from dagster_dg_cli.cli.api.shared import handle_api_errors
from dagster_dg_cli.cli.response_schema import dg_response_schema

DG_API_MAX_ASSET_LIMIT: Final = 1000
DG_API_MAX_EVENT_LIMIT: Final = 1000


@click.command(name="list", cls=DgClickCommand)
@click.option(
    "--limit",
    type=click.IntRange(1, DG_API_MAX_ASSET_LIMIT),
    default=50,
    help=f"Number of assets to return (default: 50, max: {DG_API_MAX_ASSET_LIMIT})",
)
@click.option(
    "--cursor",
    type=str,
    help="Cursor for pagination",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_rest_resources.schemas.asset", cls="DgApiAssetList")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def list_assets_command(
    ctx: click.Context,
    limit: int,
    cursor: str,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """List assets with pagination.

    Example::

        $ dg api asset list
        ASSET KEY        GROUP      DESCRIPTION                        KINDS
        raw_customers    ingestion  Customer records from Snowflake    snowflake
        stg_customers    staging    Cleaned customer records           dbt, snowflake
        dim_customers    marts      Customer dimension table           dbt, snowflake
        daily_orders     marts      Daily order aggregates             dbt, snowflake
    """
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_rest_resources.api.asset import DgApiAssetApi

    api = DgApiAssetApi(_client=client)

    with handle_api_errors(ctx, output_json):
        if limit > DG_API_MAX_ASSET_LIMIT:
            raise ValueError(f"Limit cannot exceed {DG_API_MAX_ASSET_LIMIT}")

        assets = api.list_assets(limit=limit, cursor=cursor)
        output = format_assets(assets, as_json=output_json)
        click.echo(output)


@click.command(name="get", cls=DgClickCommand)
@click.argument("asset_key", type=str)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_rest_resources.schemas.asset", cls="DgApiAsset")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_asset_command(
    ctx: click.Context,
    asset_key: str,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Get specific asset details.

    Example::

        $ dg api asset get dim_customers
        Asset Key: dim_customers
        ID: 7e4c8b2a-1f3d-4e6b-9c5a-8d2f1e3b4c7d
        Description: Customer dimension table
        Group: marts
        Kinds: dbt, snowflake
        Deps: stg_customers
    """
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_rest_resources.api.asset import DgApiAssetApi

    api = DgApiAssetApi(_client=client)

    with handle_api_errors(ctx, output_json):
        asset = api.get_asset(asset_key)
        output = format_asset(asset, as_json=output_json)
        click.echo(output)


@click.command(name="get-health", cls=DgClickCommand)
@click.argument("asset_key", type=str)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_rest_resources.schemas.asset", cls="DgApiAssetStatus")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_health_asset_command(
    ctx: click.Context,
    asset_key: str,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Get health and runtime status for an asset.

    Example::

        $ dg api asset get-health dim_customers
        Asset Key: dim_customers

        Asset Health: HEALTHY
        Materialization Status: MATERIALIZED
        Freshness Status: PASSING
        Asset Checks Status: PASSED
        Last Materialized: 2026-05-06 18:00:12 UTC
        Latest Materialization: 2026-05-06 18:00:12 UTC
        Latest Run ID: 5b3c8a91-2e4f-4d7b-9c6a-1f8d3e5b2c4a
        Total Checks: 3
        Failed Checks: 0
        Warning Checks: 0
    """
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_rest_resources.api.asset import DgApiAssetApi

    api = DgApiAssetApi(_client=client)

    with handle_api_errors(ctx, output_json):
        status = api.get_health(asset_key)
        output = format_asset_health(status, as_json=output_json)
        click.echo(output)


@click.command(name="get-events", cls=DgClickCommand)
@click.argument("asset_key", type=str)
@click.option(
    "--event-type",
    type=click.Choice(["ASSET_MATERIALIZATION", "ASSET_OBSERVATION"], case_sensitive=False),
    default=None,
    help="Filter by event type (default: both)",
)
@click.option(
    "--limit",
    type=click.IntRange(1, DG_API_MAX_EVENT_LIMIT),
    default=50,
    help=f"Max events to return (default: 50, max: {DG_API_MAX_EVENT_LIMIT})",
)
@click.option(
    "--before",
    type=str,
    default=None,
    help="Events before this ISO timestamp (e.g. 2024-01-15T00:00:00)",
)
@click.option(
    "--partition",
    "partitions",
    type=str,
    multiple=True,
    help="Filter by partition key (repeatable)",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_rest_resources.schemas.asset", cls="DgApiAssetEventList")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_events_asset_command(
    ctx: click.Context,
    asset_key: str,
    event_type: Literal["ASSET_MATERIALIZATION", "ASSET_OBSERVATION"] | None,
    limit: int,
    before: str | None,
    partitions: tuple[str, ...],
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Get materialization and observation events for an asset.

    Example::

        $ dg api asset get-events dim_customers --limit 3
        TIMESTAMP                LEVEL  TYPE                    RUN ID                                PARTITION
        2026-05-06 18:00:12 UTC  INFO   ASSET_MATERIALIZATION   5b3c8a91-2e4f-4d7b-9c6a-1f8d3e5b2c4a
        2026-05-05 18:00:08 UTC  INFO   ASSET_MATERIALIZATION   2a1f7b3c-9d8e-4c5b-8a6d-3f1e2b9c4d7a
        2026-05-04 18:00:15 UTC  INFO   ASSET_MATERIALIZATION   8c4d2e7f-1a9b-4e3d-7c5b-9f2a1d8e3b6c
    """
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_rest_resources.api.asset import DgApiAssetApi

    api = DgApiAssetApi(_client=client)

    with handle_api_errors(ctx, output_json):
        if limit > DG_API_MAX_EVENT_LIMIT:
            raise ValueError(f"Limit cannot exceed {DG_API_MAX_EVENT_LIMIT}")

        events = api.get_events(
            asset_key=asset_key,
            event_type=event_type,
            limit=limit,
            before=before,
            partitions=list(partitions) if partitions else None,
        )
        output = format_asset_events(events, as_json=output_json)
        click.echo(output)


@click.command(name="get-evaluations", cls=DgClickCommand)
@click.argument("asset_key", type=str)
@click.option(
    "--limit",
    type=click.IntRange(1, DG_API_MAX_EVENT_LIMIT),
    default=50,
    help=f"Max evaluations to return (default: 50, max: {DG_API_MAX_EVENT_LIMIT})",
)
@click.option(
    "--cursor",
    type=str,
    default=None,
    help="Cursor for pagination (evaluation ID)",
)
@click.option(
    "--include-nodes",
    is_flag=True,
    help="Include the condition evaluation node tree (verbose)",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_rest_resources.schemas.asset", cls="DgApiEvaluationRecordList")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_evaluations_asset_command(
    ctx: click.Context,
    asset_key: str,
    limit: int,
    cursor: str | None,
    include_nodes: bool,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Get automation condition evaluation records for an asset.

    Evaluations are only recorded when at least one subcondition has a different
    value than the previous evaluation.

    Example::

        $ dg api asset get-evaluations dim_customers --limit 2
        EVAL ID  TIMESTAMP                NUM REQUESTED  RUN IDS
        4218     2026-05-06 18:00:00 UTC  1              5b3c8a91-2e4f-4d7b-9c6a-1f8d3e5b2c4a
        4196     2026-05-05 18:00:00 UTC  1              2a1f7b3c-9d8e-4c5b-8a6d-3f1e2b9c4d7a
    """
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_rest_resources.api.asset import DgApiAssetApi

    api = DgApiAssetApi(_client=client)

    with handle_api_errors(ctx, output_json):
        if limit > DG_API_MAX_EVENT_LIMIT:
            raise ValueError(f"Limit cannot exceed {DG_API_MAX_EVENT_LIMIT}")

        evaluations = api.get_evaluations(
            asset_key=asset_key,
            limit=limit,
            cursor=cursor,
            include_nodes=include_nodes,
        )
        output = format_asset_evaluations(evaluations, as_json=output_json)
        click.echo(output)


@click.command(name="get-partition-status", cls=DgClickCommand)
@click.argument("asset_key", type=str)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_rest_resources.schemas.asset", cls="DgApiPartitionStats")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_partition_status_command(
    ctx: click.Context,
    asset_key: str,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Get partition materialization stats for an asset.

    Example::

        $ dg api asset get-partition-status daily_orders
        Materialized: 364
        Failed:       1
        In Progress:  0
        Total:        365
    """
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_rest_resources.api.asset import DgApiAssetApi

    api = DgApiAssetApi(_client=client)

    with handle_api_errors(ctx, output_json):
        stats = api.get_partition_status(asset_key)
        output = format_partition_status(stats, as_json=output_json)
        click.echo(output)


@click.group(
    name="asset",
    cls=DgClickGroup,
    commands={
        "list": list_assets_command,
        "get": get_asset_command,
        "get-health": get_health_asset_command,
        "get-events": get_events_asset_command,
        "get-evaluations": get_evaluations_asset_command,
        "get-partition-status": get_partition_status_command,
    },
)
def asset_group():
    """Manage assets in Dagster Plus."""
