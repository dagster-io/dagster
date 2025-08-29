"""Run API commands following GitHub CLI patterns."""

import sys

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

from dagster_dg_cli.api_layer.api.run import DgApiRunApi
from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.shared import format_error_for_output


def format_run_table(run) -> str:
    """Format run as human-readable table."""
    lines = [
        f"Run ID: {run.id}",
        f"Status: {run.status}",
        f"Created: {run.created_at}",
    ]

    if run.started_at:
        lines.append(f"Started: {run.started_at}")
    if run.ended_at:
        lines.append(f"Ended: {run.ended_at}")
    if run.pipeline_name:
        lines.append(f"Pipeline: {run.pipeline_name}")
    if run.mode:
        lines.append(f"Mode: {run.mode}")

    return "\n".join(lines)


@click.command(name="get", cls=DgClickCommand, unlaunched=True)
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
) -> None:
    """Get run metadata by ID."""
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config)
    api = DgApiRunApi(client)

    try:
        run = api.get_run(run_id)

        if output_json:
            output = run.model_dump_json(indent=2)
        else:
            output = format_run_table(run)

        click.echo(output)
    except Exception as e:
        error_output, exit_code = format_error_for_output(e, output_json)
        click.echo(error_output, err=True)
        sys.exit(exit_code)


@click.group(
    name="run",
    cls=DgClickGroup,
    unlaunched=True,
    commands={
        "get": get_run_command,
    },
)
def run_group():
    """Manage runs in Dagster Plus."""
