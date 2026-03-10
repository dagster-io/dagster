"""Issue API commands."""

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.formatters import format_issue, format_issues
from dagster_dg_cli.cli.api.shared import handle_api_errors
from dagster_dg_cli.cli.api.utils import dg_api_response_schema


@click.command(name="get", cls=DgClickCommand)
@click.argument("issue_id", type=str)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_api_response_schema(module="dagster_dg_cli.api_layer.schemas.issue", cls="DgApiIssue")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_issue_command(
    ctx: click.Context,
    issue_id: str,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Get an issue by ID."""
    from dagster_dg_cli.api_layer.api.issue import DgApiIssueApi

    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    api = DgApiIssueApi(client)

    with handle_api_errors(ctx, output_json):
        issue = api.get_issue(issue_id)
        output = format_issue(issue, as_json=output_json)
        click.echo(output)


@click.command(name="list", cls=DgClickCommand)
@click.option(
    "--limit",
    type=int,
    default=10,
    help="Number of issues to return (default: 10)",
)
@click.option(
    "--cursor",
    type=str,
    default=None,
    help="Cursor for pagination",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_api_response_schema(module="dagster_dg_cli.api_layer.schemas.issue", cls="DgApiIssueList")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def list_issues_command(
    ctx: click.Context,
    limit: int,
    cursor: str | None,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """List issues with pagination."""
    from dagster_dg_cli.api_layer.api.issue import DgApiIssueApi

    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    api = DgApiIssueApi(client)

    with handle_api_errors(ctx, output_json):
        issue_list = api.list_issues(limit=limit, cursor=cursor)
        output = format_issues(issue_list, as_json=output_json)
        click.echo(output)


@click.group(
    name="issue",
    cls=DgClickGroup,
    commands={
        "get": get_issue_command,
        "list": list_issues_command,
    },
)
def issue_group():
    """Manage issues in Dagster Plus."""
