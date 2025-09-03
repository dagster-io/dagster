"""Deployment API commands following GitHub CLI patterns."""

import json

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.deployment.formatters import format_deployments
from dagster_dg_cli.cli.api.shared import determine_output_format


@click.command(name="list", cls=DgClickCommand, unlaunched=True)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@click.option(
    "--md",
    "output_md",
    is_flag=True,
    help="Output in Markdown format for agent consumption",
)
@dg_api_options(organization_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def list_deployments_command(
    ctx: click.Context,
    output_json: bool,
    output_md: bool,
    organization: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """List all deployments in the organization."""
    output_format = determine_output_format(output_json, output_md)

    config = DagsterPlusCliConfig.create_for_organization(
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.deployments import DgApiDeploymentApi

    api = DgApiDeploymentApi(client)

    try:
        deployments = api.list_deployments()
        output = format_deployments(deployments, output_format=output_format)
        click.echo(output)
    except Exception as e:
        if output_json:
            error_response = {"error": str(e)}
            click.echo(json.dumps(error_response), err=True)
        else:
            click.echo(f"Error querying Dagster Plus API: {e}", err=True)
        raise click.ClickException(f"Failed to list deployments: {e}")


@click.group(
    name="deployment",
    cls=DgClickGroup,
    unlaunched=True,
    commands={
        "list": list_deployments_command,
    },
)
def deployment_group():
    """Manage deployments in Dagster Plus."""
