"""Deployments API commands following GitHub CLI patterns."""

import json
from typing import Any

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig


def _get_config_or_error() -> DagsterPlusCliConfig:
    if not DagsterPlusCliConfig.exists():
        raise click.UsageError(
            "`dg plus` commands require authentication with Dagster Plus. Run `dg plus login` to authenticate."
        )
    return DagsterPlusCliConfig.get()


def _format_output(data: Any, as_json: bool) -> None:
    """Format output as JSON or human-readable table."""
    if as_json:
        click.echo(json.dumps(data, indent=2))
    else:
        # Human-readable table format
        if isinstance(data, list) and data:
            for item in data:
                if isinstance(item, dict):
                    for key, value in item.items():
                        click.echo(f"{key}: {value}")
                    click.echo()  # Empty line between items
        else:
            click.echo("No data found.")


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
    from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient

    config = _get_config_or_error()

    query = """
    query CliDeploymentsQuery {
        fullDeployments {
            deploymentName
            deploymentId
            deploymentType
        }
    }
    """

    try:
        client = DagsterPlusGraphQLClient.from_config(config)
        result = client.execute(query)
        deployments = result.get("fullDeployments", [])

        # Transform to more REST-like format
        api_response = [
            {
                "name": deployment["deploymentName"],
                "id": deployment["deploymentId"],
                "type": deployment["deploymentType"],
            }
            for deployment in deployments
        ]

        _format_output(api_response, output_json)

    except Exception as e:
        if output_json:
            error_response = {"error": str(e)}
            click.echo(json.dumps(error_response), err=True)
        else:
            click.echo(f"Error querying Dagster Plus API: {e}", err=True)
        raise click.ClickException(f"Failed to list deployments: {e}")


@click.group(
    name="deployments",
    cls=DgClickGroup,
    unlaunched=True,
    commands={
        "list": list_deployments_command,
    },
)
def deployments_group():
    """Manage deployments in Dagster Plus."""
