"""Test agent business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

import json

from dagster_rest_resources.schemas.agent import (
    DgApiAgent,
    DgApiAgentList,
    DgApiAgentMetadataEntry,
    DgApiAgentStatus,
)


class TestAgentDataProcessing:
    """Test processing of agent data structures.

    This class would test any pure functions in the GraphQL adapter
    that process the raw GraphQL responses into our domain models.
    Since the actual GraphQL processing is done inline in the adapter
    functions, these tests will verify our data model creation.
    """

    def test_agent_creation_with_all_statuses(self, snapshot):
        """Test creating agents with all possible status values."""
        agents = [
            DgApiAgent(
                id=f"agent-{status.value.lower()}-uuid",
                agent_label=f"Agent {status.value.title()}",
                status=status,
                last_heartbeat_time=1641046800.0 if status == DgApiAgentStatus.RUNNING else None,
                metadata=[
                    DgApiAgentMetadataEntry(key="status_test", value=status.value),
                ],
            )
            for status in DgApiAgentStatus
        ]

        agent_list = DgApiAgentList(items=agents, total=len(agents))

        # Test JSON serialization works correctly for all statuses
        result = agent_list.model_dump_json(indent=2)

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_agent_metadata_handling(self):
        """Test agent metadata entry creation and access."""
        agent = DgApiAgent(
            id="metadata-test-agent",
            agent_label="Metadata Test",
            status=DgApiAgentStatus.RUNNING,
            last_heartbeat_time=1641046800.0,
            metadata=[
                DgApiAgentMetadataEntry(key="version", value="1.0.0"),
                DgApiAgentMetadataEntry(key="environment", value="production"),
                DgApiAgentMetadataEntry(key="region", value="us-west-2"),
            ],
        )

        assert len(agent.metadata) == 3
        assert agent.metadata[0].key == "version"
        assert agent.metadata[0].value == "1.0.0"
        assert agent.metadata[1].key == "environment"
        assert agent.metadata[1].value == "production"
        assert agent.metadata[2].key == "region"
        assert agent.metadata[2].value == "us-west-2"

    def test_agent_list_total_count(self):
        """Test that AgentList properly tracks total count."""
        agents = [
            DgApiAgent(
                id=f"agent-{i}",
                agent_label=f"Agent {i}",
                status=DgApiAgentStatus.RUNNING,
                last_heartbeat_time=None,
                metadata=[],
            )
            for i in range(3)
        ]

        agent_list = DgApiAgentList(
            items=agents, total=10
        )  # Total could be different from items length (pagination)

        assert len(agent_list.items) == 3
        assert agent_list.total == 10
