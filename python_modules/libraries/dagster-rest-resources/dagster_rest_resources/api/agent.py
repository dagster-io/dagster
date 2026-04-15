"""Agent endpoints - REST-like interface."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.graphql_adapter.agent import (
    get_agent_via_graphql,
    list_agents_via_graphql,
)

if TYPE_CHECKING:
    from dagster_rest_resources.schemas.agent import DgApiAgent, DgApiAgentList


@dataclass(frozen=True)
class DgApiAgentApi:
    client: IGraphQLClient

    def list_agents(self) -> "DgApiAgentList":
        return list_agents_via_graphql(self.client)

    def get_agent(self, agent_id: str) -> "DgApiAgent | None":
        return get_agent_via_graphql(self.client, agent_id)
