from dataclasses import dataclass

from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.agent import DgApiAgent, DgApiAgentList


@dataclass(frozen=True)
class DgApiAgentApi:
    _client: IGraphQLClient

    def list_agents(self, limit: int | None = None) -> DgApiAgentList:
        agents = self._client.list_agents().agents

        agent_list = DgApiAgentList(
            items=[
                DgApiAgent.model_validate(a, from_attributes=True)
                for a in (agents[:limit] if limit is not None else agents)
            ],
            total=len(agents),
        )

        return agent_list

    def get_agent(self, agent_id: str) -> DgApiAgent | None:
        agents = self._client.list_agents().agents
        agent = next((a for a in agents if a.id == agent_id), None)
        if agent is None:
            return None

        return DgApiAgent.model_validate(agent, from_attributes=True)
