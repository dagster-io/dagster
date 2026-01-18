"""Agent API commands following GitHub CLI patterns."""

import json

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

# Lazy import to avoid loading pydantic at CLI startup
from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.formatters import format_agent, format_agents


@click.command(name="list", cls=DgClickCommand)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_api_options(organization_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def list_agents_command(
    ctx: click.Context, output_json: bool, organization: str, api_token: str, view_graphql: bool
) -> None:
    """List all agents in the organization."""
    config = DagsterPlusCliConfig.create_for_organization(
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.agent import DgApiAgentApi

    api = DgApiAgentApi(client)

    try:
        agents = api.list_agents()
        output = format_agents(agents, as_json=output_json)
        click.echo(output)
    except Exception as e:
        if output_json:
            error_response = {"error": str(e)}
            click.echo(json.dumps(error_response), err=True)
        else:
            click.echo(f"Error querying Dagster Plus API: {e}", err=True)
        raise click.ClickException(f"Failed to list agents: {e}")


@click.command(name="get", cls=DgClickCommand)
@click.argument("agent_id", type=str)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
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
    """Get detailed information about a specific agent."""
    config = DagsterPlusCliConfig.create_for_organization(
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.agent import DgApiAgentApi

    api = DgApiAgentApi(client)

    try:
        agent = api.get_agent(agent_id)
        if agent is None:
            if output_json:
                error_response = {"error": f"Agent with ID '{agent_id}' not found"}
                click.echo(json.dumps(error_response), err=True)
            else:
                click.echo(f"Agent with ID '{agent_id}' not found", err=True)
            raise click.ClickException(f"Agent not found: {agent_id}")

        output = format_agent(agent, as_json=output_json)
        click.echo(output)
    except Exception as e:
        if output_json:
            error_response = {"error": str(e)}
            click.echo(json.dumps(error_response), err=True)
        else:
            click.echo(f"Error querying Dagster Plus API: {e}", err=True)
        raise click.ClickException(f"Failed to get agent: {e}")


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
