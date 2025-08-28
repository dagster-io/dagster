"""End-to-end error integration testing.

This module tests complete error scenarios from GraphQL responses through the API layer
to CLI output, ensuring proper error propagation and handling across all API domains.
"""

import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner
from dagster_dg_cli.cli import cli as root_cli
from dagster_dg_cli.cli.api.client import DgApiTestContext
from syrupy.assertion import SnapshotAssertion

from dagster_dg_cli_tests.cli_tests.api_tests.shared.replay_utils import ReplayClient


class TestErrorIntegration:
    """Test end-to-end error handling across all API domains."""

    @pytest.fixture
    def scenarios(self) -> dict[str, Any]:
        """Load error code test scenarios."""
        current_dir = Path(__file__).parent
        scenarios_file = current_dir / "scenarios.yaml"

        with open(scenarios_file) as f:
            scenarios = yaml.safe_load(f) or {}

        return scenarios

    @pytest.fixture
    def asset_error_scenarios(self, scenarios: dict[str, Any]) -> dict[str, Any]:
        """Filter scenarios that test asset API errors."""
        return {
            name: scenario
            for name, scenario in scenarios.items()
            if "dg api asset" in scenario["command"]
        }

    @pytest.fixture
    def deployment_error_scenarios(self, scenarios: dict[str, Any]) -> dict[str, Any]:
        """Filter scenarios that test deployment API errors."""
        return {
            name: scenario
            for name, scenario in scenarios.items()
            if "dg api deployment" in scenario["command"]
        }

    def test_complete_error_flow_json_output(
        self, scenarios: dict[str, Any], snapshot: SnapshotAssertion
    ):
        """Test complete error flow from GraphQL to JSON CLI output."""
        json_scenarios = {
            name: scenario
            for name, scenario in scenarios.items()
            if "--json" in scenario["command"]
        }

        for scenario_name, scenario in json_scenarios.items():
            # Load recorded responses for this scenario
            recordings_dir = Path(__file__).parent / "recordings"
            scenario_folder = recordings_dir / scenario_name

            # Skip if recording doesn't exist
            if not scenario_folder.exists():
                pytest.skip(
                    f"Recording not found for {scenario_name}. Run: make record SCENARIO={scenario_name}"
                )

            # Load all recorded responses
            from dagster_dg_cli_tests.cli_tests.api_tests.shared.replay_utils import (
                load_recorded_graphql_responses,
            )

            try:
                recorded_responses = load_recorded_graphql_responses(recordings_dir, scenario_name)
            except ValueError:
                pytest.skip(f"No valid recordings found for {scenario_name}")

            # Create test context with recorded responses
            replay_client = ReplayClient(recorded_responses)
            test_context = DgApiTestContext(client_factory=lambda config: replay_client)

            # Execute command
            runner = CliRunner()
            command_args = scenario["command"].split()[1:]  # Remove 'dg'
            result = runner.invoke(root_cli, command_args, obj=test_context, catch_exceptions=False)

            # Create snapshot data
            snapshot_data = {
                "scenario": scenario_name,
                "command": scenario["command"],
                "exit_code": result.exit_code,
                "output": result.output,
                "expected_code": scenario.get("expected_code"),
                "expected_status": scenario.get("expected_status"),
                "description": scenario.get("description"),
            }

            # Assert against snapshot
            assert snapshot_data == snapshot(name=f"json_error_flow_{scenario_name}")

    def test_complete_error_flow_text_output(
        self, scenarios: dict[str, Any], snapshot: SnapshotAssertion
    ):
        """Test complete error flow from GraphQL to text CLI output."""
        text_scenarios = {
            name: scenario
            for name, scenario in scenarios.items()
            if "--json" not in scenario["command"]
        }

        for scenario_name, scenario in text_scenarios.items():
            # Load recorded responses for this scenario
            recordings_dir = Path(__file__).parent / "recordings"
            scenario_folder = recordings_dir / scenario_name

            # Skip if recording doesn't exist
            if not scenario_folder.exists():
                pytest.skip(
                    f"Recording not found for {scenario_name}. Run: make record SCENARIO={scenario_name}"
                )

            # Load all recorded responses
            from dagster_dg_cli_tests.cli_tests.api_tests.shared.replay_utils import (
                load_recorded_graphql_responses,
            )

            try:
                recorded_responses = load_recorded_graphql_responses(recordings_dir, scenario_name)
            except ValueError:
                pytest.skip(f"No valid recordings found for {scenario_name}")

            # Create test context with recorded responses
            replay_client = ReplayClient(recorded_responses)
            test_context = DgApiTestContext(client_factory=lambda config: replay_client)

            # Execute command
            runner = CliRunner()
            command_args = scenario["command"].split()[1:]  # Remove 'dg'
            result = runner.invoke(root_cli, command_args, obj=test_context, catch_exceptions=False)

            # Create snapshot data
            snapshot_data = {
                "scenario": scenario_name,
                "command": scenario["command"],
                "exit_code": result.exit_code,
                "output": result.output,
                "expected_code": scenario.get("expected_code"),
                "expected_status": scenario.get("expected_status"),
                "description": scenario.get("description"),
            }

            # Assert against snapshot
            assert snapshot_data == snapshot(name=f"text_error_flow_{scenario_name}")

    def test_cross_domain_error_consistency(self, scenarios: dict[str, Any]):
        """Test that similar errors are handled consistently across different API domains."""
        # Group scenarios by error type
        error_groups = {}

        for scenario_name, scenario in scenarios.items():
            expected_code = scenario.get("expected_code")
            if expected_code:
                if expected_code not in error_groups:
                    error_groups[expected_code] = []
                error_groups[expected_code].append((scenario_name, scenario))

        # Test consistency within each error group
        for error_code, scenarios_in_group in error_groups.items():
            if len(scenarios_in_group) < 2:
                continue  # Need at least 2 scenarios to test consistency

            # Check that all scenarios with same error code have same status
            expected_statuses = set()
            for scenario_name, scenario in scenarios_in_group:
                expected_status = scenario.get("expected_status")
                if expected_status:
                    expected_statuses.add(expected_status)

            assert len(expected_statuses) <= 1, (
                f"Error code {error_code} has inconsistent status codes: {expected_statuses}"
            )

    def test_error_propagation_through_api_layers(self, asset_error_scenarios: dict[str, Any]):
        """Test that errors properly propagate through API layers without mutation."""
        for scenario_name, scenario in asset_error_scenarios.items():
            # Load recorded responses
            recordings_dir = Path(__file__).parent / "recordings"

            if not (recordings_dir / scenario_name).exists():
                continue

            try:
                from dagster_dg_cli_tests.cli_tests.api_tests.shared.replay_utils import (
                    load_recorded_graphql_responses,
                )

                recorded_responses = load_recorded_graphql_responses(recordings_dir, scenario_name)
            except (ValueError, IndexError):
                continue

            # Test that GraphQL errors in response are properly handled
            if "errors" in recorded_responses[0]:
                # Create test context
                replay_client = ReplayClient(recorded_responses)
                test_context = DgApiTestContext(client_factory=lambda config: replay_client)

                # Execute command
                runner = CliRunner()
                command_args = scenario["command"].split()[1:]  # Remove 'dg'
                result = runner.invoke(
                    root_cli, command_args, obj=test_context, catch_exceptions=False
                )

                # Should exit with error
                assert result.exit_code != 0, (
                    f"Command should fail when GraphQL errors present in {scenario_name}"
                )

                # If JSON output, should have proper error structure
                if "--json" in scenario["command"]:
                    try:
                        error_response = json.loads(result.output)
                        assert "error" in error_response, (
                            f"JSON error response should have 'error' field in {scenario_name}"
                        )
                        assert "code" in error_response, (
                            f"JSON error response should have 'code' field in {scenario_name}"
                        )
                    except json.JSONDecodeError:
                        pytest.fail(f"Invalid JSON output for {scenario_name}")

    def test_fallback_error_handling(self, scenarios: dict[str, Any]):
        """Test fallback behavior for unknown or malformed error responses."""
        # Test with completely empty response
        empty_response = {}

        # Pick a representative scenario
        representative_scenario = None
        for scenario_name, scenario in scenarios.items():
            if "--json" in scenario["command"]:
                representative_scenario = (scenario_name, scenario)
                break

        if not representative_scenario:
            pytest.skip("No JSON scenario found for fallback testing")

        scenario_name, scenario = representative_scenario

        # Create test context with empty response
        replay_client = ReplayClient([empty_response])
        test_context = DgApiTestContext(client_factory=lambda config: replay_client)

        # Execute command
        runner = CliRunner()
        command_args = scenario["command"].split()[1:]  # Remove 'dg'

        # This should not crash, should handle gracefully
        try:
            result = runner.invoke(root_cli, command_args, obj=test_context, catch_exceptions=False)
            # Should exit with some kind of error code
            assert result.exit_code != 0, "Empty response should result in error"
        except Exception:
            # If it does crash, this is a test failure - fallback should handle gracefully
            pytest.fail("Command crashed on empty response - fallback handling insufficient")

    def test_error_message_localization_consistency(self, scenarios: dict[str, Any]):
        """Test that error messages are consistent and properly localized."""
        for scenario_name, scenario in scenarios.items():
            # Load recorded responses
            recordings_dir = Path(__file__).parent / "recordings"

            if not (recordings_dir / scenario_name).exists():
                continue

            try:
                from dagster_dg_cli_tests.cli_tests.api_tests.shared.replay_utils import (
                    load_recorded_graphql_responses,
                )

                recorded_responses = load_recorded_graphql_responses(recordings_dir, scenario_name)
            except (ValueError, IndexError):
                continue

            # Create test context
            replay_client = ReplayClient(recorded_responses)
            test_context = DgApiTestContext(client_factory=lambda config: replay_client)

            # Execute command
            runner = CliRunner()
            command_args = scenario["command"].split()[1:]  # Remove 'dg'
            result = runner.invoke(root_cli, command_args, obj=test_context, catch_exceptions=False)

            if result.exit_code == 0:
                continue  # Skip successful commands

            # Error messages should be in English and properly formatted
            output = result.output.strip()
            if output:
                # Should not contain raw GraphQL error markup
                assert "<" not in output, (
                    f"Error message contains markup in {scenario_name}: {output}"
                )
                assert ">" not in output, (
                    f"Error message contains markup in {scenario_name}: {output}"
                )

                # Should not contain internal Python paths or stack traces
                assert "Traceback" not in output, (
                    f"Error message contains traceback in {scenario_name}"
                )
                assert "/python" not in output.lower(), (
                    f"Error message contains path in {scenario_name}"
                )

    def test_concurrent_error_handling(self, scenarios: dict[str, Any]):
        """Test that error handling is consistent under concurrent access patterns."""
        # This is a placeholder for future concurrent testing
        # For now, just ensure error handling doesn't have shared state issues

        json_scenarios = [
            (name, scenario)
            for name, scenario in scenarios.items()
            if "--json" in scenario["command"]
        ][:3]  # Test with first 3 JSON scenarios

        results = []

        for scenario_name, scenario in json_scenarios:
            # Load recorded responses
            recordings_dir = Path(__file__).parent / "recordings"

            if not (recordings_dir / scenario_name).exists():
                continue

            try:
                from dagster_dg_cli_tests.cli_tests.api_tests.shared.replay_utils import (
                    load_recorded_graphql_responses,
                )

                recorded_responses = load_recorded_graphql_responses(recordings_dir, scenario_name)
            except (ValueError, IndexError):
                continue

            # Create test context
            replay_client = ReplayClient(recorded_responses)
            test_context = DgApiTestContext(client_factory=lambda config: replay_client)

            # Execute command
            runner = CliRunner()
            command_args = scenario["command"].split()[1:]  # Remove 'dg'
            result = runner.invoke(root_cli, command_args, obj=test_context, catch_exceptions=False)

            results.append((scenario_name, result.exit_code, result.output))

        # Each execution should be independent - no shared state corruption
        for i, (scenario_name, exit_code, output) in enumerate(results):
            assert exit_code != 0, f"Error scenario {scenario_name} should fail"
            assert output.strip(), f"Error scenario {scenario_name} should have output"
