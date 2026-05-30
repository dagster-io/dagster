"""Issue API commands."""

import datetime

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_rest_resources.schemas.enums import DgApiIssueStatus
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.formatters import format_issue, format_issues
from dagster_dg_cli.cli.api.shared import handle_api_errors
from dagster_dg_cli.cli.response_schema import dg_response_schema


@click.command(name="get", cls=DgClickCommand)
@click.argument("issue_id", type=str)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_rest_resources.schemas.issue", cls="DgApiIssue")
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
    """Get an issue by ID.

    Example::

        $ dg api issue get 7e2c44b9-8f1a-4d6e-b0c3-2a5f9d4e6b18
        Title:       Snowflake load failed for daily_orders
        Status:      OPEN
        Created By:  oncall@example.com
        Run IDs:     5b3c8a91-2e4f-4d7b-9c6a-1f8d3e5b2c4a
        Asset Keys:  daily_orders
        Description: Snowflake permission denied while loading partition 2026-05-06
    """
    from dagster_rest_resources.api.issue import DgApiIssueApi

    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    api = DgApiIssueApi(_client=client)

    with handle_api_errors(ctx, output_json):
        issue = api.get_issue(issue_id=issue_id)
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
    "--status",
    "statuses",
    multiple=True,
    type=click.Choice([e.value for e in DgApiIssueStatus], case_sensitive=False),
    callback=lambda ctx, param, values: tuple(DgApiIssueStatus(v.upper()) for v in values),
    help="Filter by issue status. Repeatable.",
)
@click.option(
    "--created-after",
    type=click.DateTime(formats=["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"]),
    default=None,
    help="Filter issues created after this date (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
)
@click.option(
    "--created-before",
    type=click.DateTime(formats=["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"]),
    default=None,
    help="Filter issues created before this date (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_rest_resources.schemas.issue", cls="DgApiIssueList")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def list_issues_command(
    ctx: click.Context,
    limit: int,
    cursor: str | None,
    statuses: tuple[DgApiIssueStatus, ...],
    created_after: datetime.datetime | None,
    created_before: datetime.datetime | None,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """List issues with pagination and optional filtering.

    Example::

        $ dg api issue list --limit 3 --status OPEN
        STATUS  TITLE                                       ID                                    CREATED BY
        OPEN    Snowflake load failed for daily_orders      7e2c44b9-8f1a-4d6e-b0c3-2a5f9d4e6b18  oncall@example.com
        OPEN    Stale freshness on stg_customers            ad9c7f2e-3b15-4a87-9d61-5c8b3e2f1a04  alice@example.com
        OPEN    dbt test failure: unique_customer_id        c0b1ab17-1d2e-4f5b-9c8a-3e8d2c5f7a91  bob@example.com
    """
    from dagster_rest_resources.api.issue import DgApiIssueApi

    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )

    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    api = DgApiIssueApi(_client=client)

    with handle_api_errors(ctx, output_json):
        issue_list = api.list_issues(
            limit=limit,
            cursor=cursor,
            statuses=list(statuses) if statuses else None,
            created_after=created_after.timestamp() if created_after else None,
            created_before=created_before.timestamp() if created_before else None,
        )
        output = format_issues(issue_list, as_json=output_json)
        click.echo(output)


@click.command(name="create", cls=DgClickCommand)
@click.option(
    "--title",
    type=str,
    required=True,
    help="Title of the issue",
)
@click.option(
    "--description",
    type=str,
    required=True,
    help="Description of the issue",
)
@click.option(
    "--status",
    type=click.Choice([e.value for e in DgApiIssueStatus], case_sensitive=False),
    callback=lambda ctx, param, v: DgApiIssueStatus(v.upper()) if v else None,
    default=None,
    help="Status of the issue. Defaults to 'OPEN'",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_dg_cli.api_layer.schemas.issue", cls="DgApiIssue")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def create_issue_command(
    ctx: click.Context,
    title: str,
    description: str,
    status: DgApiIssueStatus | None,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Create a new issue.

    Example::

        $ dg api issue create --title "Snowflake load failed" --description "Permission denied loading daily_orders"
        Title:       Snowflake load failed
        Status:      OPEN
        Created By:  oncall@example.com
        Description: Permission denied loading daily_orders
    """
    from dagster_rest_resources.api.issue import DgApiIssueApi

    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    api = DgApiIssueApi(_client=client)

    with handle_api_errors(ctx, output_json):
        issue = api.create_issue(title=title, description=description, status=status)
        output = format_issue(issue, as_json=output_json)
        click.echo(output)


@click.command(name="update", cls=DgClickCommand)
@click.argument("issue_id", type=str)
@click.option(
    "--status",
    type=click.Choice([e.value for e in DgApiIssueStatus], case_sensitive=False),
    callback=lambda ctx, param, v: DgApiIssueStatus(v.upper()) if v else None,
    default=None,
    help="New status for the issue",
)
@click.option(
    "--title",
    type=str,
    default=None,
    help="New title for the issue",
)
@click.option(
    "--description",
    type=str,
    default=None,
    help="New description for the issue",
)
@click.option(
    "--context",
    type=str,
    default=None,
    help="Additional context for the issue",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_dg_cli.api_layer.schemas.issue", cls="DgApiIssue")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def update_issue_command(
    ctx: click.Context,
    issue_id: str,
    status: DgApiIssueStatus | None,
    title: str | None,
    description: str | None,
    context: str | None,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Update an existing issue.

    Example::

        $ dg api issue update 7e2c44b9-8f1a-4d6e-b0c3-2a5f9d4e6b18 --status RESOLVED
        Title:       Snowflake load failed for daily_orders
        Status:      RESOLVED
        Created By:  oncall@example.com
        Description: Snowflake permission denied while loading partition 2026-05-06
    """
    from dagster_rest_resources.api.issue import DgApiIssueApi

    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    api = DgApiIssueApi(_client=client)

    with handle_api_errors(ctx, output_json):
        issue = api.update_issue(
            issue_id=issue_id,
            status=status,
            title=title,
            description=description,
            context=context,
        )
        output = format_issue(issue, as_json=output_json)
        click.echo(output)


@click.command(name="add-link", cls=DgClickCommand)
@click.argument("issue_id", type=str)
@click.option(
    "--run-id",
    type=str,
    default=None,
    help="Run ID to link to the issue",
)
@click.option(
    "--asset-key",
    type=str,
    default=None,
    help="Asset key to link to the issue (slash-separated path, e.g. 'my/asset')",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_rest_resources.schemas.issue", cls="DgApiIssue")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def add_link_issue_command(
    ctx: click.Context,
    issue_id: str,
    run_id: str | None,
    asset_key: str | None,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Add a run or asset link to an issue.

    Example::

        $ dg api issue add-link 7e2c44b9-8f1a-4d6e-b0c3-2a5f9d4e6b18 --run-id 5b3c8a91-2e4f-4d7b-9c6a-1f8d3e5b2c4a
        Title:       Snowflake load failed for daily_orders
        Status:      OPEN
        Created By:  oncall@example.com
        Run IDs:     5b3c8a91-2e4f-4d7b-9c6a-1f8d3e5b2c4a
        Description: Snowflake permission denied while loading partition 2026-05-06
    """
    from dagster_rest_resources.api.issue import DgApiIssueApi

    if run_id is None and asset_key is None:
        raise click.UsageError("At least one of --run-id or --asset-key must be provided.")

    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    api = DgApiIssueApi(_client=client)

    with handle_api_errors(ctx, output_json):
        issue = api.create_link_on_issue(
            issue_id=issue_id,
            run_id=run_id,
            asset_key=asset_key.split("/") if asset_key else None,
        )
        output = format_issue(issue, as_json=output_json)
        click.echo(output)


@click.command(name="remove-link", cls=DgClickCommand)
@click.argument("issue_id", type=str)
@click.option(
    "--run-id",
    type=str,
    default=None,
    help="Run ID to unlink from the issue",
)
@click.option(
    "--asset-key",
    type=str,
    default=None,
    help="Asset key to unlink from the issue (slash-separated path, e.g. 'my/asset')",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_rest_resources.schemas.issue", cls="DgApiIssue")
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def remove_link_issue_command(
    ctx: click.Context,
    issue_id: str,
    run_id: str | None,
    asset_key: str | None,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Remove a run or asset link from an issue.

    Example::

        $ dg api issue remove-link 7e2c44b9-8f1a-4d6e-b0c3-2a5f9d4e6b18 --run-id 5b3c8a91-2e4f-4d7b-9c6a-1f8d3e5b2c4a
        Title:       Snowflake load failed for daily_orders
        Status:      OPEN
        Created By:  oncall@example.com
        Description: Snowflake permission denied while loading partition 2026-05-06
    """
    from dagster_rest_resources.api.issue import DgApiIssueApi

    if run_id is None and asset_key is None:
        raise click.UsageError("At least one of --run-id or --asset-key must be provided.")

    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    api = DgApiIssueApi(_client=client)

    with handle_api_errors(ctx, output_json):
        issue = api.delete_link_from_issue(
            issue_id=issue_id,
            run_id=run_id,
            asset_key=asset_key.split("/") if asset_key else None,
        )
        output = format_issue(issue, as_json=output_json)
        click.echo(output)


@click.group(
    name="issue",
    cls=DgClickGroup,
    commands={
        "add-link": add_link_issue_command,
        "create": create_issue_command,
        "get": get_issue_command,
        "list": list_issues_command,
        "remove-link": remove_link_issue_command,
        "update": update_issue_command,
    },
)
def issue_group():
    """Manage issues in Dagster Plus."""
