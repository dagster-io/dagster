"""Job API commands following GitHub CLI patterns."""

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.formatters import format_job, format_jobs
from dagster_dg_cli.cli.api.shared import handle_api_errors
from dagster_dg_cli.cli.response_schema import dg_response_schema


@click.command(name="list", cls=DgClickCommand)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_dg_cli.api_layer.schemas.job", cls="DgApiJobList")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def list_jobs_command(
    ctx: click.Context,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """List jobs in the deployment."""
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.job import DgApiJobApi

    api = DgApiJobApi(client)

    with handle_api_errors(ctx, output_json):
        jobs = api.list_jobs()
        output = format_jobs(jobs, as_json=output_json)
        click.echo(output)


@click.command(name="get", cls=DgClickCommand)
@click.argument("job_name", type=str)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_dg_cli.api_layer.schemas.job", cls="DgApiJob")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_job_command(
    ctx: click.Context,
    job_name: str,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Get specific job details."""
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.job import DgApiJobApi

    api = DgApiJobApi(client)

    with handle_api_errors(ctx, output_json):
        job = api.get_job_by_name(job_name=job_name)
        output = format_job(job, as_json=output_json)
        click.echo(output)


@click.group(
    name="job",
    cls=DgClickGroup,
    commands={
        "list": list_jobs_command,
        "get": get_job_command,
    },
)
def job_group():
    """Manage jobs in Dagster Plus."""
