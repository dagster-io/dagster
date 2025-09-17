"""Test agent business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

from dagster_dg_cli.api_layer.schemas.agent import Agent, AgentList, AgentMetadataEntry, AgentStatus
from dagster_dg_cli.cli.api.formatters import format_agent, format_agents


class TestFormatAgents:
    """Test the agent formatting functions."""

    def _create_sample_agent_list(self):
        """Create sample AgentList for testing."""
        agents = [
            Agent(
                id="agent-1-uuid-12345",
                agent_label="Production Agent",
                status=AgentStatus.RUNNING,
                last_heartbeat_time=1641046800.0,  # 2022-01-01 14:20:00 UTC (midday to avoid timezone edge cases)
                metadata=[
                    AgentMetadataEntry(key="version", value="1.2.3"),
                    AgentMetadataEntry(key="location", value="us-east-1"),
                ],
            ),
            Agent(
                id="agent-2-uuid-67890",
                agent_label=None,  # No label - should fall back to ID display
                status=AgentStatus.STOPPED,
                last_heartbeat_time=None,
                metadata=[],
            ),
            Agent(
                id="agent-3-uuid-abcdef",
                agent_label="Staging Agent",
                status=AgentStatus.UNHEALTHY,
                last_heartbeat_time=1641046860.0,  # 2022-01-01 14:21:00 UTC
                metadata=[
                    AgentMetadataEntry(key="environment", value="staging"),
                ],
            ),
        ]
        return AgentList(items=agents, total=3)

    def _create_empty_agent_list(self):
        """Create empty AgentList for testing."""
        return AgentList(items=[], total=0)

    def _create_single_agent(self):
        """Create single Agent for testing."""
        return Agent(
            id="single-agent-uuid-xyz",
            agent_label="Development Agent",
            status=AgentStatus.RUNNING,
            last_heartbeat_time=1641046800.0,
            metadata=[
                AgentMetadataEntry(key="owner", value="dev-team"),
                AgentMetadataEntry(key="cpu_limit", value="2"),
                AgentMetadataEntry(key="memory_limit", value="4Gi"),
            ],
        )

    def test_format_agents_text_output(self, snapshot):
        """Test formatting agents as text."""
        from dagster_shared.utils.timing import fixed_timezone

        agent_list = self._create_sample_agent_list()
        with fixed_timezone("UTC"):
            result = format_agents(agent_list, as_json=False)

        # Snapshot the entire text output
        snapshot.assert_match(result)

    def test_format_agents_json_output(self, snapshot):
        """Test formatting agents as JSON."""
        agent_list = self._create_sample_agent_list()
        result = format_agents(agent_list, as_json=True)

        # For JSON, we want to snapshot the parsed structure to avoid formatting differences
        import json

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_empty_agents_text_output(self, snapshot):
        """Test formatting empty agent list as text."""
        agent_list = self._create_empty_agent_list()
        result = format_agents(agent_list, as_json=False)

        snapshot.assert_match(result)

    def test_format_empty_agents_json_output(self, snapshot):
        """Test formatting empty agent list as JSON."""
        agent_list = self._create_empty_agent_list()
        result = format_agents(agent_list, as_json=True)

        import json

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_single_agent_text_output(self, snapshot):
        """Test formatting single agent as text."""
        from dagster_shared.utils.timing import fixed_timezone

        agent = self._create_single_agent()
        with fixed_timezone("UTC"):
            result = format_agent(agent, as_json=False)

        snapshot.assert_match(result)

    def test_format_single_agent_json_output(self, snapshot):
        """Test formatting single agent as JSON."""
        agent = self._create_single_agent()
        result = format_agent(agent, as_json=True)

        import json

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_agent_without_metadata(self, snapshot):
        """Test formatting agent with no metadata."""
        from dagster_shared.utils.timing import fixed_timezone

        agent = Agent(
            id="simple-agent-uuid",
            agent_label="Simple Agent",
            status=AgentStatus.NOT_RUNNING,
            last_heartbeat_time=None,
            metadata=[],
        )
        with fixed_timezone("UTC"):
            result = format_agent(agent, as_json=False)

        snapshot.assert_match(result)

    def test_format_agent_without_label(self, snapshot):
        """Test formatting agent with no label (should use ID fallback)."""
        from dagster_shared.utils.timing import fixed_timezone

        agent = Agent(
            id="no-label-agent-uuid-123456789",
            agent_label=None,
            status=AgentStatus.UNKNOWN,
            last_heartbeat_time=1641046920.0,  # 2022-01-01 14:22:00 UTC
            metadata=[
                AgentMetadataEntry(key="type", value="serverless"),
            ],
        )
        with fixed_timezone("UTC"):
            result = format_agent(agent, as_json=False)

        snapshot.assert_match(result)


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
            Agent(
                id=f"agent-{status.value.lower()}-uuid",
                agent_label=f"Agent {status.value.title()}",
                status=status,
                last_heartbeat_time=1641046800.0 if status == AgentStatus.RUNNING else None,
                metadata=[
                    AgentMetadataEntry(key="status_test", value=status.value),
                ],
            )
            for status in AgentStatus
        ]

        agent_list = AgentList(items=agents, total=len(agents))

        # Test JSON serialization works correctly for all statuses
        result = agent_list.model_dump_json(indent=2)
        import json

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_agent_metadata_handling(self):
        """Test agent metadata entry creation and access."""
        agent = Agent(
            id="metadata-test-agent",
            agent_label="Metadata Test",
            status=AgentStatus.RUNNING,
            last_heartbeat_time=1641046800.0,
            metadata=[
                AgentMetadataEntry(key="version", value="1.0.0"),
                AgentMetadataEntry(key="environment", value="production"),
                AgentMetadataEntry(key="region", value="us-west-2"),
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
            Agent(
                id=f"agent-{i}",
                agent_label=f"Agent {i}",
                status=AgentStatus.RUNNING,
                last_heartbeat_time=None,
                metadata=[],
            )
            for i in range(3)
        ]

        agent_list = AgentList(
            items=agents, total=10
        )  # Total could be different from items length (pagination)

        assert len(agent_list.items) == 3
        assert agent_list.total == 10

    def test_agent_id_fallback_display(self):
        """Test agent display label fallback behavior."""
        # Test with label
        agent_with_label = Agent(
            id="very-long-agent-uuid-12345678901234567890",
            agent_label="Custom Label",
            status=AgentStatus.RUNNING,
            last_heartbeat_time=None,
            metadata=[],
        )

        # Test without label
        agent_without_label = Agent(
            id="very-long-agent-uuid-12345678901234567890",
            agent_label=None,
            status=AgentStatus.RUNNING,
            last_heartbeat_time=None,
            metadata=[],
        )

        # Format both agents and check the label display
        result_with_label = format_agent(agent_with_label, as_json=False)
        result_without_label = format_agent(agent_without_label, as_json=False)

        assert "Label: Custom Label" in result_with_label
        assert "Label: Agent very-lon" in result_without_label  # Should show first 8 chars
