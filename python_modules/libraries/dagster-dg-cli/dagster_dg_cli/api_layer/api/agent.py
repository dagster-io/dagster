"""Agent endpoints - REST-like interface."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from dagster_dg_cli.api_layer.graphql_adapter.agent import (
    get_agent_via_graphql,
    list_agents_via_graphql,
)
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.agent import DgApiAgent, DgApiAgentList


@dataclass(frozen=True)
class DgApiAgentApi:
    client: IGraphQLClient

    def list_agents(self) -> "DgApiAgentList":
        return list_agents_via_graphql(self.client)

    def get_agent(self, agent_id: str) -> Optional["DgApiAgent"]:
        return get_agent_via_graphql(self.client, agent_id)
