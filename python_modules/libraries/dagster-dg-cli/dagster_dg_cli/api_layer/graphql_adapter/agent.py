"""GraphQL implementation for agent operations."""

from typing import TYPE_CHECKING, Any, Optional

from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.agent import DgApiAgent, DgApiAgentList

# GraphQL queries
LIST_AGENTS_QUERY = """
query ListAgents {
    agents {
        id
        agentLabel
        status
        lastHeartbeatTime
        metadata {
            key
            value
        }
    }
}
"""

# Note: There's no single 'agent' query, so we use 'agents' and filter client-side


def process_agents_response(graphql_response: dict[str, Any]) -> "DgApiAgentList":
    """Process GraphQL response into AgentList.

    This is a pure function that can be easily tested without mocking GraphQL clients.

    Args:
        graphql_response: Raw GraphQL response containing "agents"

    Returns:
        AgentList: Processed agent data
    """
    # Import pydantic models only when needed
    from dagster_dg_cli.api_layer.schemas.agent import (
        DgApiAgent,
        DgApiAgentList,
        DgApiAgentMetadataEntry,
        DgApiAgentStatus,
    )

    agents_data = graphql_response.get("agents", [])

    agents = []
    for a in agents_data:
        metadata = [
            DgApiAgentMetadataEntry(key=m["key"], value=m["value"]) for m in a.get("metadata", [])
        ]

        agents.append(
            DgApiAgent(
                id=a["id"],
                agent_label=a.get("agentLabel"),
                status=DgApiAgentStatus[a["status"]],
                last_heartbeat_time=a.get("lastHeartbeatTime"),
                metadata=metadata,
            )
        )

    return DgApiAgentList(
        items=agents,
        total=len(agents),
    )


def list_agents_via_graphql(
    client: IGraphQLClient,
    limit: Optional[int] = None,
) -> "DgApiAgentList":
    """Fetch agents using GraphQL.
    This is an implementation detail that can be replaced with REST calls later.
    """
    result = client.execute(LIST_AGENTS_QUERY)

    agent_list = process_agents_response(result)

    # Apply limit if specified
    if limit is not None:
        agent_list.items = agent_list.items[:limit]
        agent_list.total = len(agent_list.items)

    return agent_list


def get_agent_via_graphql(
    client: IGraphQLClient,
    agent_id: str,
) -> Optional["DgApiAgent"]:
    """Fetch single agent using GraphQL.
    This is an implementation detail that can be replaced with REST calls later.

    Note: Since there's no single 'agent' query, we fetch all agents and filter client-side.
    """
    result = client.execute(LIST_AGENTS_QUERY)
    agent_list = process_agents_response(result)

    # Find the agent with matching ID
    for agent in agent_list.items:
        if agent.id == agent_id:
            return agent

    return None
