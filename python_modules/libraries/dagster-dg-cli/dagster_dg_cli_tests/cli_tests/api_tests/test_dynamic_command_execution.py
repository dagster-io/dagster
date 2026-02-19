import json
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner
from dagster_dg_cli.cli.api.client import DgApiTestContext
from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient

from dagster_dg_cli_tests.cli_tests.api_tests.shared.yaml_loader import (
    load_fixture_scenarios_from_yaml,
)


class ReplayClient(DagsterPlusGraphQLClient):
    """GraphQL client that replays recorded responses."""

    def __init__(self, responses: list[dict[str, Any]]):
        # Don't call super().__init__ as we don't need the real GraphQL client
        self.responses = responses
        self.call_index = 0

    def execute(self, query: str, variables: Mapping[str, Any] | None = None) -> dict:
        """Return next recorded response."""
        if self.call_index >= len(self.responses):
            raise ValueError(f"Exhausted {len(self.responses)} responses")
        response = self.responses[self.call_index]
        self.call_index += 1
        return response


def discover_scenario_recordings() -> Iterator[tuple[str, str, str, bool]]:
    """Discover all scenario recordings across API test domains."""
    api_tests_dir = Path(__file__).parent

    domain_dirs = [d for d in api_tests_dir.iterdir() if d.is_dir() and d.name.endswith("_tests")]

    for domain_dir in domain_dirs:
        scenarios_yaml = domain_dir / "scenarios.yaml"
        if not scenarios_yaml.exists():
            continue

        domain = domain_dir.name.replace("_tests", "")
        recording_scenarios = load_fixture_scenarios_from_yaml(scenarios_yaml)

        for scenario_name, scenario_config in recording_scenarios.items():
            yield (domain, scenario_name, scenario_config.command, scenario_config.has_recording)


def load_recorded_graphql_responses(domain: str, scenario_name: str) -> list[dict[str, Any]]:
    """Load GraphQL response recordings for a given domain and scenario."""
    scenario_folder = Path(__file__).parent / f"{domain}_tests" / "recordings" / scenario_name

    if not scenario_folder.exists():
        raise ValueError(f"Recording scenario not found: {scenario_folder}")

    json_files = sorted([f for f in scenario_folder.glob("*.json") if f.name[0:2].isdigit()])

    if not json_files:
        raise ValueError(f"No numbered JSON files found in {scenario_folder}")

    responses = []
    for json_file in json_files:
        with open(json_file) as f:
            responses.append(json.load(f))

    return responses


class TestDynamicCommandExecution:
    """Test all commands from YAML scenarios against recorded GraphQL responses."""

    @pytest.mark.parametrize(
        "domain,scenario_name,command,has_recording", list(discover_scenario_recordings())
    )
    def test_command_execution(
        self, domain: str, scenario_name: str, command: str, has_recording: bool, snapshot
    ):
        """Test executing a command against its recorded GraphQL responses.

        Uses Click's dependency injection to provide a test client factory.
        No mocking required - just inject a context with our replay client.
        """
        from dagster_dg_cli.cli import cli as root_cli
        from dagster_shared.utils.timing import fixed_timezone

        # Load GraphQL responses for this scenario
        graphql_responses = (
            load_recorded_graphql_responses(domain, scenario_name) if has_recording else []
        )

        # Create replay client
        replay_client = ReplayClient(graphql_responses)

        # Create context with test factory
        test_context = DgApiTestContext(client_factory=lambda config: replay_client)

        # Run command with injected context - SINGLE INJECTION POINT
        runner = CliRunner()
        args = command.split()[1:]  # Skip 'dg'

        # This is necessary because some commands output formatted timestamps that don't include
        # timezone info. Fixing the timezone ensures consistent output across environments.
        with fixed_timezone("UTC"):
            # Click's obj parameter passes our context through
            result = runner.invoke(root_cli, args, obj=test_context)

        # Snapshot testing
        output_type = "json" if "--json" in command else "text"
        snapshot_name = f"{domain}_{scenario_name}_{output_type}"

        if "--json" in command:
            try:
                parsed_output = json.loads(result.output)
                assert parsed_output == snapshot(name=snapshot_name)
            except json.JSONDecodeError:
                assert result.output == snapshot(name=snapshot_name)
        else:
            assert result.output == snapshot(name=snapshot_name)

        if "error" not in scenario_name.lower():
            assert result.exit_code == 0
