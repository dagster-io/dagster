"""Run API commands following GitHub CLI patterns."""

import json
from typing import Optional

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

# Lazy import to avoid loading pydantic at CLI startup
from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.formatters import format_run, format_runs


@click.command(name="list", cls=DgClickCommand, unlaunched=True)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@click.option(
    "--status",
    help="Filter by run status (e.g., SUCCESS, FAILURE, STARTED)",
)
@click.option(
    "--job",
    "job_name",
    help="Filter by job name",
)
@click.option(
    "--limit",
    type=int,
    help="Maximum number of runs to return",
)
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def list_runs_command(
    ctx: click.Context,
    output_json: bool,
    status: Optional[str],
    job_name: Optional[str],
    limit: Optional[int],
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """List runs in the deployment."""
    config = DagsterPlusCliConfig.create_for_deployment(
        organization=organization,
        deployment=deployment,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.runs import DgApiRunApi

    api = DgApiRunApi(client)

    try:
        runs = api.list_runs(
            limit=limit,
            status=status,
            job_name=job_name,
        )
        output = format_runs(runs, as_json=output_json)
        click.echo(output)
    except Exception as e:
        if output_json:
            error_response = {"error": str(e)}
            click.echo(json.dumps(error_response), err=True)
        else:
            click.echo(f"Error querying Dagster Plus API: {e}", err=True)
        raise click.ClickException(f"Failed to list runs: {e}")


@click.command(name="get", cls=DgClickCommand, unlaunched=True)
@click.argument("run_id", required=True)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_run_command(
    ctx: click.Context,
    run_id: str,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Get detailed information about a specific run."""
    config = DagsterPlusCliConfig.create_for_deployment(
        organization=organization,
        deployment=deployment,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.runs import DgApiRunApi

    api = DgApiRunApi(client)

    try:
        run = api.get_run(run_id)
        output = format_run(run, as_json=output_json)
        click.echo(output)
    except Exception as e:
        if output_json:
            error_response = {"error": str(e)}
            click.echo(json.dumps(error_response), err=True)
        else:
            click.echo(f"Error querying Dagster Plus API: {e}", err=True)
        raise click.ClickException(f"Failed to get run: {e}")


@click.group(
    name="run",
    cls=DgClickGroup,
    unlaunched=True,
    commands={
        "list": list_runs_command,
        "get": get_run_command,
    },
)
def run_group():
    """Manage runs in Dagster Plus."""
