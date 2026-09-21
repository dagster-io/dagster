from unittest.mock import Mock

from dagster_rest_resources.__generated__.enums import AgentStatus
from dagster_rest_resources.__generated__.list_agents import (
    ListAgents,
    ListAgentsAgents,
    ListAgentsAgentsMetadata,
)
from dagster_rest_resources.api.agent import DgApiAgentApi
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.agent import DgApiAgentList


class TestListAgents:
    def test_returns_agents(self):
        client = Mock(spec=IGraphQLClient)
        client.list_agents.return_value = ListAgents(
            agents=[
                ListAgentsAgents(
                    id="agent-1",
                    agentLabel="Agent One",
                    status=AgentStatus.RUNNING,
                    lastHeartbeatTime=1234567890.0,
                    metadata=[ListAgentsAgentsMetadata(key="version", value="1.0.0")],
                )
            ]
        )
        result = DgApiAgentApi(_client=client).list_agents()

        assert len(result.items) == 1
        assert result.total == 1
        assert result.items[0].id == "agent-1"
        assert result.items[0].status == AgentStatus.RUNNING
        assert result.items[0].metadata[0].key == "version"
        assert result.items[0].metadata[0].value == "1.0.0"

    def test_returns_no_agents(self):
        client = Mock(spec=IGraphQLClient)
        client.list_agents.return_value = ListAgents(agents=[])
        result = DgApiAgentApi(_client=client).list_agents()

        assert result == DgApiAgentList(items=[], total=0)


class TestGetAgent:
    def test_returns_matching_agent(self):
        client = Mock(spec=IGraphQLClient)
        client.list_agents.return_value = ListAgents(
            agents=[
                ListAgentsAgents(
                    id="agent-1",
                    agentLabel="Agent One",
                    status=AgentStatus.RUNNING,
                    lastHeartbeatTime=1234567890.0,
                    metadata=[],
                ),
                ListAgentsAgents(
                    id="agent-2",
                    agentLabel="Agent Two",
                    status=AgentStatus.NOT_RUNNING,
                    lastHeartbeatTime=1234567890.0,
                    metadata=[],
                ),
            ]
        )
        result = DgApiAgentApi(_client=client).get_agent("agent-2")

        assert result is not None
        assert result.id == "agent-2"
        assert result.status == AgentStatus.NOT_RUNNING

    def test_returns_none_when_no_matching_agent(self):
        client = Mock(spec=IGraphQLClient)
        client.list_agents.return_value = ListAgents(
            agents=[
                ListAgentsAgents(
                    id="agent-1",
                    agentLabel="Agent One",
                    status=AgentStatus.RUNNING,
                    lastHeartbeatTime=1234567890.0,
                    metadata=[],
                )
            ]
        )
        result = DgApiAgentApi(_client=client).get_agent("nonexistent")

        assert result is None
