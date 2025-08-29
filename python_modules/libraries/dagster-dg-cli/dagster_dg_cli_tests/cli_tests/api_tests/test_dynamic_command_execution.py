"""Dynamic test execution from scenarios.yaml fixtures.

This test module automatically discovers all scenarios defined in scenarios.yaml files
across API test domains and runs them against their recorded GraphQL response fixtures.
"""

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from dagster_dg_cli_tests.cli_tests.api_tests.shared.yaml_loader import (
    load_fixture_scenarios_from_yaml,
)


def discover_scenario_fixtures() -> Iterator[tuple[str, str, str]]:
    """Discover all scenario fixtures across API test domains.

    Returns:
        Iterator of (domain, fixture_name, command) tuples
    """
    api_tests_dir = Path(__file__).parent

    # Find all domain test directories
    domain_dirs = [d for d in api_tests_dir.iterdir() if d.is_dir() and d.name.endswith("_tests")]

    for domain_dir in domain_dirs:
        scenarios_yaml = domain_dir / "fixtures" / "scenarios.yaml"
        if not scenarios_yaml.exists():
            continue

        domain = domain_dir.name.replace("_tests", "")
        fixture_scenarios = load_fixture_scenarios_from_yaml(scenarios_yaml)

        for fixture_name, fixture_config in fixture_scenarios.items():
            yield (domain, fixture_name, fixture_config.command)


def get_command_mapping() -> dict[str, Any]:
    """Map command strings to their corresponding Click command objects.

    Returns:
        Dictionary mapping command patterns to Click commands
    """
    # Import CLI commands
    from dagster_dg_cli.cli.api.deployment import list_deployments_command

    return {
        "dg api deployment list": list_deployments_command,
        # TODO: Add more command mappings as needed
    }


def parse_command_string(command: str) -> tuple[Any, list[str]]:
    """Parse a command string to extract the Click command and arguments.

    Args:
        command: Full command string (e.g., "dg api deployment list --json")

    Returns:
        Tuple of (click_command, args_list)

    Raises:
        ValueError: If command is not recognized
    """
    command_mapping = get_command_mapping()

    # Split command and look for matches
    parts = command.split()

    # Try to find the longest matching command prefix
    for i in range(len(parts), 0, -1):
        prefix = " ".join(parts[:i])
        if prefix in command_mapping:
            click_command = command_mapping[prefix]
            remaining_args = parts[i:]
            return click_command, remaining_args

    raise ValueError(f"No matching Click command found for: {command}")


def load_fixture_graphql_responses(domain: str, fixture_name: str) -> list[dict[str, Any]]:
    """Load GraphQL response fixtures for a given domain and fixture.

    Args:
        domain: API domain (e.g., 'deployment', 'asset')
        fixture_name: Name of the fixture scenario

    Returns:
        List of GraphQL response dictionaries
    """
    if domain == "deployment":
        from dagster_dg_cli_tests.cli_tests.api_tests.deployment_tests.fixtures import (
            load_deployment_response_fixture,
        )

        return load_deployment_response_fixture(fixture_name)
    # TODO: Add other domains as they become available
    else:
        raise ValueError(f"Unknown domain: {domain}")


class TestDynamicCommandExecution:
    """Test all commands from YAML fixtures against recorded GraphQL responses."""

    @pytest.mark.parametrize("domain,fixture_name,command", list(discover_scenario_fixtures()))
    def test_command_execution(self, domain: str, fixture_name: str, command: str, snapshot):
        """Test executing a command against its recorded GraphQL responses."""
        try:
            # Parse the command
            click_command, args = parse_command_string(command)

            # Load GraphQL responses for this fixture
            graphql_responses = load_fixture_graphql_responses(domain, fixture_name)

            # Mock the GraphQL client based on domain
            if domain == "deployment":
                result = self._test_deployment_command(
                    click_command, args, graphql_responses, fixture_name
                )

                # Create a unique snapshot name based on fixture and output type
                output_type = "json" if "--json" in args else "text"
                snapshot_name = f"{domain}_{fixture_name}_{output_type}"

                # Use syrupy to snapshot the CLI output with custom name
                if "--json" in args:
                    # For JSON output, parse and snapshot the structure
                    try:
                        parsed_output = json.loads(result.output)
                        assert parsed_output == snapshot(name=snapshot_name)
                    except json.JSONDecodeError:
                        # For error cases, snapshot the raw output
                        assert result.output == snapshot(name=snapshot_name)
                else:
                    # For text output, snapshot the raw CLI output
                    assert result.output == snapshot(name=snapshot_name)

                # Keep existing exit code assertions for safety
                if "error" not in fixture_name.lower():
                    assert result.exit_code == 0
            else:
                pytest.skip(f"Domain '{domain}' not yet supported in dynamic tests")

        except Exception as e:
            pytest.fail(f"Failed to execute command '{command}' for fixture '{fixture_name}': {e}")

    def _test_deployment_command(
        self, click_command: Any, args: list[str], graphql_responses: list[dict], fixture_name: str
    ):
        """Test a deployment domain command with mocked GraphQL responses."""
        with patch("dagster_dg_cli.cli.api.shared.get_config_or_error") as mock_config:
            with patch(
                "dagster_dg_cli.dagster_plus_api.graphql_adapter.deployment.DagsterPlusGraphQLClient.from_config"
            ) as mock_client_class:
                # Setup mocks
                mock_config.return_value = "mock-config"
                mock_client = mock_client_class.return_value
                mock_client.execute.return_value = graphql_responses[0]

                # Execute command
                runner = CliRunner()
                result = runner.invoke(click_command, args)

                # Return the result for snapshot testing
                return result
