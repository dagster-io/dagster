"""Deployment API commands following GitHub CLI patterns."""

import json

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper

from dagster_dg_cli.cli.api.formatters import format_deployments
from dagster_dg_cli.cli.api.shared import get_config_or_error
from dagster_dg_cli.dagster_plus_api.api.deployments import DgApiDeploymentApi


@click.command(name="list", cls=DgClickCommand, unlaunched=True)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@cli_telemetry_wrapper
def list_deployments_command(output_json: bool) -> None:
    """List all deployments in the organization."""
    config = get_config_or_error()
    api = DgApiDeploymentApi(config)

    try:
        deployments = api.list_deployments()
        output = format_deployments(deployments, as_json=output_json)
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
