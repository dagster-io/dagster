"""Agent API commands following GitHub CLI patterns."""

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

# Lazy import to avoid loading pydantic at CLI startup
from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.formatters import format_agent, format_agents
from dagster_dg_cli.cli.api.shared import handle_api_errors
from dagster_dg_cli.cli.response_schema import dg_response_schema


@click.command(name="list", cls=DgClickCommand)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_rest_resources.schemas.agent", cls="DgApiAgentList")
@dg_api_options(organization_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def list_agents_command(
    ctx: click.Context, output_json: bool, organization: str, api_token: str, view_graphql: bool
) -> None:
    """List all agents in the organization.

    Example::

        $ dg api agent list
        LABEL              ID                                    STATUS   LAST HEARTBEAT
        analytics-prod-1   c0b1ab17-1d2e-4f5b-9c8a-3e8d2c5f7a91  RUNNING  2026-05-06 18:42:11 UTC
        ingest-prod        7e2c44b9-8f1a-4d6e-b0c3-2a5f9d4e6b18  RUNNING  2026-05-06 18:42:08 UTC
        Agent ad9c7f2e     ad9c7f2e-3b15-4a87-9d61-5c8b3e2f1a04  STOPPED  2026-05-05 22:17:35 UTC
    """
    config = DagsterPlusCliConfig.create_for_organization(
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_rest_resources.api.agent import DgApiAgentApi

    api = DgApiAgentApi(client)

    with handle_api_errors(ctx, output_json):
        agents = api.list_agents()
        output = format_agents(agents, as_json=output_json)
        click.echo(output)


@click.command(name="get", cls=DgClickCommand)
@click.argument("agent_id", type=str)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(module="dagster_rest_resources.schemas.agent", cls="DgApiAgent")
@dg_api_options(organization_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_agent_command(
    ctx: click.Context,
    agent_id: str,
    output_json: bool,
    organization: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Get detailed information about a specific agent.

    Example::

        $ dg api agent get c0b1ab17-1d2e-4f5b-9c8a-3e8d2c5f7a91
        Label:          analytics-prod-1
        ID:             c0b1ab17-1d2e-4f5b-9c8a-3e8d2c5f7a91
        Status:         RUNNING
        Last Heartbeat: 2026-05-06 18:42:11 UTC

        Metadata:
          version: 1.12.0
          dagster_cloud_version: 1.12.0
    """
    config = DagsterPlusCliConfig.create_for_organization(
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_rest_resources.api.agent import DgApiAgentApi

    api = DgApiAgentApi(client)

    with handle_api_errors(ctx, output_json):
        agent = api.get_agent(agent_id)
        if agent is None:
            raise click.ClickException(f"Agent not found: {agent_id}")

        output = format_agent(agent, as_json=output_json)
        click.echo(output)


@click.group(
    name="agent",
    cls=DgClickGroup,
    commands={
        "list": list_agents_command,
        "get": get_agent_command,
    },
)
def agent_group():
    """Manage agents in Dagster Plus."""
