"""Asset check API commands following GitHub CLI patterns."""

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.formatters import format_asset_check_executions, format_asset_checks
from dagster_dg_cli.cli.api.shared import handle_api_errors
from dagster_dg_cli.cli.response_schema import dg_response_schema


@click.command(name="list", cls=DgClickCommand)
@click.option(
    "--asset-key",
    required=True,
    type=str,
    help="Slash-separated asset key (e.g., my/asset)",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(
    module="dagster_dg_cli.api_layer.schemas.asset_check", cls="DgApiAssetCheckList"
)
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def list_asset_checks_command(
    ctx: click.Context,
    asset_key: str,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """List asset checks for an asset."""
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.asset_check import DgApiAssetCheckApi

    api = DgApiAssetCheckApi(client)

    with handle_api_errors(ctx, output_json):
        checks = api.list_asset_checks(asset_key=asset_key)
        output = format_asset_checks(checks, as_json=output_json)
        click.echo(output)


@click.command(name="get-executions", cls=DgClickCommand)
@click.option(
    "--asset-key",
    required=True,
    type=str,
    help="Slash-separated asset key (e.g., my/asset)",
)
@click.option(
    "--check-name",
    required=True,
    type=str,
    help="Name of the asset check",
)
@click.option(
    "--limit",
    type=int,
    default=25,
    help="Maximum number of executions to return (default: 25)",
)
@click.option(
    "--cursor",
    type=str,
    help="Pagination cursor",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(
    module="dagster_dg_cli.api_layer.schemas.asset_check", cls="DgApiAssetCheckExecutionList"
)
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_asset_check_executions_command(
    ctx: click.Context,
    asset_key: str,
    check_name: str,
    limit: int,
    cursor: str | None,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Get execution history for an asset check."""
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.asset_check import DgApiAssetCheckApi

    api = DgApiAssetCheckApi(client)

    with handle_api_errors(ctx, output_json):
        executions = api.get_check_executions(
            asset_key=asset_key,
            check_name=check_name,
            limit=limit,
            cursor=cursor,
        )
        output = format_asset_check_executions(executions, as_json=output_json)
        click.echo(output)


@click.group(
    name="asset-check",
    cls=DgClickGroup,
    commands={
        "list": list_asset_checks_command,
        "get-executions": get_asset_check_executions_command,
    },
)
def asset_check_group():
    """Manage asset checks in Dagster Plus."""
