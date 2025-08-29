"""Test error response structure and format validation.

This module tests that all error responses follow proper structure conventions
for both JSON and text output formats, and that exit codes are correct.
"""

import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner
from dagster_dg_cli.cli import cli as root_cli
from dagster_dg_cli.cli.api.shared import DgApiTestContext

from dagster_dg_cli_tests.cli_tests.api_tests.shared.replay_utils import ReplayClient


class TestErrorStructure:
    """Test error response structure and formatting."""

    @pytest.fixture
    def scenarios(self) -> dict[str, Any]:
        """Load error code test scenarios."""
        current_dir = Path(__file__).parent
        scenarios_file = current_dir / "scenarios.yaml"

        with open(scenarios_file) as f:
            scenarios = yaml.safe_load(f) or {}

        return scenarios

    @pytest.fixture
    def json_error_scenarios(self, scenarios: dict[str, Any]) -> dict[str, Any]:
        """Filter scenarios that use JSON output format."""
        return {
            name: scenario
            for name, scenario in scenarios.items()
            if "--json" in scenario["command"]
        }

    @pytest.fixture
    def text_error_scenarios(self, scenarios: dict[str, Any]) -> dict[str, Any]:
        """Filter scenarios that use text output format."""
        return {
            name: scenario
            for name, scenario in scenarios.items()
            if "--json" not in scenario["command"]
        }

    def test_json_error_response_structure(self, json_error_scenarios: dict[str, Any]):
        """Test that JSON error responses have correct structure.

        All JSON error responses must contain:
        - error: Human-readable error message
        - code: Machine-readable error code
        - statusCode: HTTP status code
        - type: Error type category
        """
        for scenario_name, scenario in json_error_scenarios.items():
            # Load recorded response for this scenario
            recordings_dir = Path(__file__).parent / "recordings" / scenario_name
            response_file = recordings_dir / "01_response.json"

            # Skip if recording doesn't exist (test will fail later when recording is attempted)
            if not response_file.exists():
                pytest.skip(
                    f"Recording not found for {scenario_name}. Run: make record SCENARIO={scenario_name}"
                )

            with open(response_file) as f:
                recorded_response = json.load(f)

            # Create test context with recorded response
            replay_client = ReplayClient([recorded_response])
            test_context = DgApiTestContext(client_factory=lambda config: replay_client)

            # Execute command
            runner = CliRunner()
            command_args = scenario["command"].split()[1:]  # Remove 'dg'
            result = runner.invoke(root_cli, command_args, obj=test_context, catch_exceptions=False)

            # Should exit with error
            assert result.exit_code != 0, f"Command should fail for error scenario {scenario_name}"

            # Parse JSON output
            try:
                error_response = json.loads(result.output)
            except json.JSONDecodeError:
                pytest.fail(f"Invalid JSON in error response for {scenario_name}: {result.output}")

            # Validate required fields
            required_fields = {"error", "code", "statusCode", "type"}
            missing_fields = required_fields - set(error_response.keys())
            assert not missing_fields, (
                f"Missing required fields in {scenario_name}: {missing_fields}"
            )

            # Validate field types
            assert isinstance(error_response["error"], str), (
                f"'error' must be string in {scenario_name}"
            )
            assert isinstance(error_response["code"], str), (
                f"'code' must be string in {scenario_name}"
            )
            assert isinstance(error_response["statusCode"], int), (
                f"'statusCode' must be int in {scenario_name}"
            )
            assert isinstance(error_response["type"], str), (
                f"'type' must be string in {scenario_name}"
            )

            # Validate expected values
            expected_code = scenario.get("expected_code")
            expected_status = scenario.get("expected_status")

            if expected_code:
                assert error_response["code"] == expected_code, (
                    f"Expected code {expected_code}, got {error_response['code']} in {scenario_name}"
                )

            if expected_status:
                assert error_response["statusCode"] == expected_status, (
                    f"Expected status {expected_status}, got {error_response['statusCode']} in {scenario_name}"
                )

    def test_text_error_response_format(self, text_error_scenarios: dict[str, Any]):
        """Test that text error responses have consistent format.

        Text error responses should:
        - Start with "Error querying Dagster Plus API: "
        - Contain human-readable error message
        - Be written to stderr
        """
        for scenario_name, scenario in text_error_scenarios.items():
            # Load recorded response for this scenario
            recordings_dir = Path(__file__).parent / "recordings" / scenario_name
            response_file = recordings_dir / "01_response.json"

            # Skip if recording doesn't exist
            if not response_file.exists():
                pytest.skip(
                    f"Recording not found for {scenario_name}. Run: make record SCENARIO={scenario_name}"
                )

            with open(response_file) as f:
                recorded_response = json.load(f)

            # Create test context with recorded response
            replay_client = ReplayClient([recorded_response])
            test_context = DgApiTestContext(client_factory=lambda config: replay_client)

            # Execute command
            runner = CliRunner()
            command_args = scenario["command"].split()[1:]  # Remove 'dg'
            result = runner.invoke(root_cli, command_args, obj=test_context, catch_exceptions=False)

            # Should exit with error
            assert result.exit_code != 0, f"Command should fail for error scenario {scenario_name}"

            # Error message should be in stderr output (Click captures this in result.output)
            assert result.output, f"No error output for {scenario_name}"
            assert result.output.startswith("Error querying Dagster Plus API: "), (
                f"Text error format incorrect for {scenario_name}: {result.output}"
            )

    def test_exit_code_mapping(self, scenarios: dict[str, Any]):
        """Test that exit codes properly reflect HTTP status codes.

        Exit codes should map as follows:
        - 4xx errors -> exit code 1 (client error)
        - 5xx errors -> exit code 5 (server error)
        """
        for scenario_name, scenario in scenarios.items():
            expected_status = scenario.get("expected_status")
            if not expected_status:
                continue

            # Load recorded response for this scenario
            recordings_dir = Path(__file__).parent / "recordings" / scenario_name
            response_file = recordings_dir / "01_response.json"

            # Skip if recording doesn't exist
            if not response_file.exists():
                pytest.skip(
                    f"Recording not found for {scenario_name}. Run: make record SCENARIO={scenario_name}"
                )

            with open(response_file) as f:
                recorded_response = json.load(f)

            # Create test context with recorded response
            replay_client = ReplayClient([recorded_response])
            test_context = DgApiTestContext(client_factory=lambda config: replay_client)

            # Execute command
            runner = CliRunner()
            command_args = scenario["command"].split()[1:]  # Remove 'dg'
            result = runner.invoke(root_cli, command_args, obj=test_context, catch_exceptions=False)

            # Map status code to expected exit code
            expected_exit_code = expected_status // 100  # 4xx -> 4, 5xx -> 5
            if expected_exit_code == 4:
                expected_exit_code = 1  # Client errors use exit code 1
            elif expected_exit_code == 5:
                expected_exit_code = 5  # Server errors use exit code 5
            else:
                expected_exit_code = 1  # Default to 1 for other errors

            assert result.exit_code == expected_exit_code, (
                f"Expected exit code {expected_exit_code} for status {expected_status}, got {result.exit_code} in {scenario_name}"
            )

    def test_error_type_categorization(self, json_error_scenarios: dict[str, Any]):
        """Test that error type field correctly categorizes errors.

        Error types should match status codes:
        - 400 -> client_error
        - 401 -> authentication_error
        - 403 -> authorization_error
        - 404 -> not_found_error
        - 422 -> migration_error
        - 500 -> server_error
        """
        status_to_type = {
            400: "client_error",
            401: "authentication_error",
            403: "authorization_error",
            404: "not_found_error",
            422: "migration_error",
            500: "server_error",
        }

        for scenario_name, scenario in json_error_scenarios.items():
            expected_status = scenario.get("expected_status")
            if not expected_status:
                continue

            # Load recorded response for this scenario
            recordings_dir = Path(__file__).parent / "recordings" / scenario_name
            response_file = recordings_dir / "01_response.json"

            # Skip if recording doesn't exist
            if not response_file.exists():
                continue

            with open(response_file) as f:
                recorded_response = json.load(f)

            # Create test context with recorded response
            replay_client = ReplayClient([recorded_response])
            test_context = DgApiTestContext(client_factory=lambda config: replay_client)

            # Execute command
            runner = CliRunner()
            command_args = scenario["command"].split()[1:]  # Remove 'dg'
            result = runner.invoke(root_cli, command_args, obj=test_context, catch_exceptions=False)

            # Parse JSON output
            try:
                error_response = json.loads(result.output)
            except json.JSONDecodeError:
                continue

            # Validate error type matches status code
            expected_type = status_to_type.get(expected_status, "server_error")
            actual_type = error_response.get("type")

            assert actual_type == expected_type, (
                f"Expected error type {expected_type} for status {expected_status}, got {actual_type} in {scenario_name}"
            )

    def test_error_message_non_empty(self, scenarios: dict[str, Any]):
        """Test that all error messages are non-empty and descriptive."""
        for scenario_name, scenario in scenarios.items():
            # Load recorded response for this scenario
            recordings_dir = Path(__file__).parent / "recordings" / scenario_name
            response_file = recordings_dir / "01_response.json"

            # Skip if recording doesn't exist
            if not response_file.exists():
                continue

            with open(response_file) as f:
                recorded_response = json.load(f)

            # Create test context with recorded response
            replay_client = ReplayClient([recorded_response])
            test_context = DgApiTestContext(client_factory=lambda config: replay_client)

            # Execute command
            runner = CliRunner()
            command_args = scenario["command"].split()[1:]  # Remove 'dg'
            result = runner.invoke(root_cli, command_args, obj=test_context, catch_exceptions=False)

            # Should exit with error and have output
            assert result.exit_code != 0, f"Command should fail for error scenario {scenario_name}"
            assert result.output.strip(), f"Error message should not be empty for {scenario_name}"

            # For JSON responses, validate error field
            if "--json" in scenario["command"]:
                try:
                    error_response = json.loads(result.output)
                    error_message = error_response.get("error", "")
                    assert error_message and error_message.strip(), (
                        f"JSON error message should not be empty for {scenario_name}"
                    )
                except json.JSONDecodeError:
                    pass  # Will be caught by other tests
