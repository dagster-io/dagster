"""Run API commands following GitHub CLI patterns."""

import json

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client


def format_run_table(run) -> str:
    """Format run as human-readable table."""
    lines = [
        f"Run ID: {run.id}",
        f"Status: {run.status.value}",
        f"Created: {run.created_at}",
    ]

    if run.started_at:
        lines.append(f"Started: {run.started_at}")
    if run.ended_at:
        lines.append(f"Ended: {run.ended_at}")
    if run.job_name:
        lines.append(f"Pipeline: {run.job_name}")

    return "\n".join(lines)


@click.command(name="get", cls=DgClickCommand)
@click.argument("run_id", type=str)
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
    """Get run metadata by ID."""
    from dagster_dg_cli.api_layer.api.run import DgApiRunApi

    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    api = DgApiRunApi(client)

    try:
        run = api.get_run(run_id)

        if output_json:
            output = run.model_dump_json(indent=2)
        else:
            output = format_run_table(run)

        click.echo(output)
    except Exception as e:
        if output_json:
            error_response = {"error": str(e)}
            click.echo(json.dumps(error_response), err=True)
        else:
            click.echo(f"Error querying Dagster Plus API: {e}", err=True)


@click.group(
    name="run",
    cls=DgClickGroup,
    commands={
        "get": get_run_command,
    },
)
def run_group():
    """Manage runs in Dagster Plus."""
