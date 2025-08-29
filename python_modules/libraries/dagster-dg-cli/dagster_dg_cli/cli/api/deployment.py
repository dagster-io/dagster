"""Deployment API commands following GitHub CLI patterns."""

import sys

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper

# Lazy import to avoid loading pydantic at CLI startup
from dagster_dg_cli.cli.api.client import create_dg_api_client
from dagster_dg_cli.cli.api.formatters import format_deployments
from dagster_dg_cli.cli.api.shared import format_error_for_output


@click.command(name="list", cls=DgClickCommand, unlaunched=True)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@cli_telemetry_wrapper
@click.pass_context
def list_deployments_command(ctx: click.Context, output_json: bool) -> None:
    """List all deployments in the organization."""
    client = create_dg_api_client(ctx)
    from dagster_dg_cli.api_layer.api.deployments import DgApiDeploymentApi

    api = DgApiDeploymentApi(client)

    try:
        deployments = api.list_deployments()
        output = format_deployments(deployments, as_json=output_json)
        click.echo(output)
    except Exception as e:
        error_output, exit_code = format_error_for_output(e, output_json)
        click.echo(error_output, err=True)
        sys.exit(exit_code)


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
