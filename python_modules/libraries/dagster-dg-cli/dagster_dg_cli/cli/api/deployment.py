"""Deployment API commands following GitHub CLI patterns."""

import sys

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper

from dagster_dg_cli.cli.api.formatters import format_deployments
from dagster_dg_cli.cli.api.shared import format_error_for_output, get_config_or_error
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
