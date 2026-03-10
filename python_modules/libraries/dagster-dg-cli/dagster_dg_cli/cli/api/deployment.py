"""Deployment API commands following GitHub CLI patterns."""

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

# Lazy import to avoid loading pydantic at CLI startup
from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.formatters import format_deployment, format_deployments
from dagster_dg_cli.cli.api.shared import handle_api_errors
from dagster_dg_cli.cli.response_schema import dg_response_schema


@click.command(name="list", cls=DgClickCommand)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_dg_cli.api_layer.schemas.deployment", cls="DeploymentList")
@dg_api_options(organization_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def list_deployments_command(
    ctx: click.Context, output_json: bool, organization: str, api_token: str, view_graphql: bool
) -> None:
    """List all deployments in the organization."""
    config = DagsterPlusCliConfig.create_for_organization(
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.deployments import DgApiDeploymentApi

    api = DgApiDeploymentApi(client)

    with handle_api_errors(ctx, output_json):
        deployments = api.list_deployments()
        output = format_deployments(deployments, as_json=output_json)
        click.echo(output)


@click.command(name="get", cls=DgClickCommand)
@click.argument("name", required=True)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_dg_cli.api_layer.schemas.deployment", cls="Deployment")
@dg_api_options(organization_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_deployment_command(
    ctx: click.Context,
    name: str,
    output_json: bool,
    organization: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Show detailed information about a specific deployment."""
    config = DagsterPlusCliConfig.create_for_organization(
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.deployments import DgApiDeploymentApi

    api = DgApiDeploymentApi(client)

    with handle_api_errors(ctx, output_json):
        try:
            deployment = api.get_deployment(name)
        except ValueError as e:
            if "Deployment not found" in str(e):
                raise click.ClickException(f"Deployment '{name}' not found")
            else:
                raise
        output = format_deployment(deployment, as_json=output_json)
        click.echo(output)


@click.group(
    name="deployment",
    cls=DgClickGroup,
    commands={
        "list": list_deployments_command,
        "get": get_deployment_command,
    },
)
def deployment_group():
    """Manage deployments in Dagster Plus."""
