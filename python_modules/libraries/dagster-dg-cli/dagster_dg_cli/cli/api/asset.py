"""Asset API commands following GitHub CLI patterns."""

import json
from typing import Final

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
    format_assets,
)
from dagster_dg_cli.cli.api.utils import dg_api_response_schema

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
    "--status",
    is_flag=True,
    help="Include health and runtime status information",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_api_response_schema(module="dagster_dg_cli.api_layer.schemas.asset", cls="DgApiAssetList")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def list_assets_command(
    ctx: click.Context,
    limit: int,
    cursor: str,
    status: bool,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """List assets with pagination."""
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.asset import DgApiAssetApi

    api = DgApiAssetApi(client)

    try:
        assets = api.list_assets(limit=limit, cursor=cursor, status=status)
        output = format_assets(assets, as_json=output_json)
        click.echo(output)
    except Exception as e:
        if output_json:
            error_response = {"error": str(e)}
            click.echo(json.dumps(error_response), err=True)
        else:
            click.echo(f"Error querying Dagster Plus API: {e}", err=True)
        raise click.ClickException(f"Failed to list assets: {e}")


@click.command(name="get", cls=DgClickCommand)
@click.argument("asset_key", type=str)
@click.option(
    "--status",
    is_flag=True,
    help="Include health and runtime status information",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_api_response_schema(module="dagster_dg_cli.api_layer.schemas.asset", cls="DgApiAsset")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_asset_command(
    ctx: click.Context,
    asset_key: str,
    status: bool,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Get specific asset details."""
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.asset import DgApiAssetApi

    api = DgApiAssetApi(client)

    try:
        asset = api.get_asset(asset_key, status=status)
        output = format_asset(asset, as_json=output_json)
        click.echo(output)
    except Exception as e:
        if output_json:
            error_response = {"error": str(e)}
            click.echo(json.dumps(error_response), err=True)
        else:
            click.echo(f"Error querying Dagster Plus API: {e}", err=True)
        raise click.ClickException(f"Failed to get asset: {e}")


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
@dg_api_response_schema(module="dagster_dg_cli.api_layer.schemas.asset", cls="DgApiAssetEventList")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_events_asset_command(
    ctx: click.Context,
    asset_key: str,
    event_type: str | None,
    limit: int,
    before: str | None,
    partitions: tuple[str, ...],
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Get materialization and observation events for an asset."""
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.asset import DgApiAssetApi

    api = DgApiAssetApi(client)

    try:
        events = api.get_events(
            asset_key=asset_key,
            event_type=event_type.upper() if event_type else None,
            limit=limit,
            before=before,
            partitions=list(partitions) if partitions else None,
        )
        output = format_asset_events(events, as_json=output_json)
        click.echo(output)
    except Exception as e:
        if output_json:
            error_response = {"error": str(e)}
            click.echo(json.dumps(error_response), err=True)
        else:
            click.echo(f"Error querying Dagster Plus API: {e}", err=True)
        raise click.ClickException(f"Failed to get asset events: {e}")


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
@dg_api_response_schema(
    module="dagster_dg_cli.api_layer.schemas.asset", cls="DgApiEvaluationRecordList"
)
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
    """
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.asset import DgApiAssetApi

    api = DgApiAssetApi(client)

    try:
        evaluations = api.get_evaluations(
            asset_key=asset_key,
            limit=limit,
            cursor=cursor,
            include_nodes=include_nodes,
        )
        output = format_asset_evaluations(evaluations, as_json=output_json)
        click.echo(output)
    except Exception as e:
        if output_json:
            error_response = {"error": str(e)}
            click.echo(json.dumps(error_response), err=True)
        else:
            click.echo(f"Error querying Dagster Plus API: {e}", err=True)
        raise click.ClickException(f"Failed to get asset evaluations: {e}")


@click.group(
    name="asset",
    cls=DgClickGroup,
    commands={
        "list": list_assets_command,
        "get": get_asset_command,
        "get-events": get_events_asset_command,
        "get-evaluations": get_evaluations_asset_command,
    },
)
def asset_group():
    """Manage assets in Dagster Plus."""
