"""Asset API commands following GitHub CLI patterns."""

import sys

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.formatters import format_asset, format_assets
from dagster_dg_cli.cli.api.shared import format_error_for_output


@click.command(name="list", cls=DgClickCommand, unlaunched=True)
@click.option(
    "--limit",
    type=click.IntRange(1, 1000),
    default=50,
    help="Number of assets to return (default: 50, max: 1000)",
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
) -> None:
    """List assets with pagination."""
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config)
    from dagster_dg_cli.api_layer.api.asset import DgApiAssetApi

    api = DgApiAssetApi(client)

    try:
        assets = api.list_assets(limit=limit, cursor=cursor)
        output = format_assets(assets, as_json=output_json)
        click.echo(output)
    except Exception as e:
        error_output, exit_code = format_error_for_output(e, output_json)
        click.echo(error_output, err=True)
        sys.exit(exit_code)


@click.command(name="get", cls=DgClickCommand, unlaunched=True)
@click.argument("asset_key", type=str)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
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
) -> None:
    """Get specific asset details."""
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config)
    from dagster_dg_cli.api_layer.api.asset import DgApiAssetApi

    api = DgApiAssetApi(client)

    try:
        asset = api.get_asset(asset_key)
        output = format_asset(asset, as_json=output_json)
        click.echo(output)
    except Exception as e:
        error_output, exit_code = format_error_for_output(e, output_json)
        click.echo(error_output, err=True)
        sys.exit(exit_code)


@click.group(
    name="asset",
    cls=DgClickGroup,
    unlaunched=True,
    commands={
        "list": list_assets_command,
        "get": get_asset_command,
    },
)
def asset_group():
    """Manage assets in Dagster Plus."""
