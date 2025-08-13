"""Integration tests for deployment list command.

These tests focus on CLI behavior and use minimal mocking of the GraphQL client
to test the integration between components.
"""

import json
from unittest.mock import patch

from click.testing import CliRunner
from dagster_dg_cli.cli.api.deployment import list_deployments_command

from dagster_dg_cli_tests.cli_tests.api_tests.deployment_tests.fixtures import (
    load_deployment_response_fixture,
)


class TestDeploymentListCommand:
    """Test the deployment list CLI command integration."""

    @patch("dagster_dg_cli.cli.api.deployment._get_config_or_error")
    @patch(
        "dagster_dg_cli.dagster_plus_api.graphql_adapter.deployment.DagsterPlusGraphQLClient.from_config"
    )
    def test_list_deployments_text_output(self, mock_client_class, mock_config, snapshot):
        """Test successful deployment list with text output."""
        # Setup mocks
        mock_config.return_value = "mock-config"
        mock_client = mock_client_class.return_value
        mock_client.execute.return_value = load_deployment_response_fixture(
            "success_multiple_deployments"
        )

        # Run command
        runner = CliRunner()
        result = runner.invoke(list_deployments_command, [])

        # Verify success
        assert result.exit_code == 0

        # Verify GraphQL was called with correct query
        mock_client.execute.assert_called_once()
        called_query = mock_client.execute.call_args[0][0]
        assert "query ListDeployments" in called_query
        assert "fullDeployments" in called_query

        # Snapshot the CLI output
        snapshot.assert_match(result.output)

    @patch("dagster_dg_cli.cli.api.deployment._get_config_or_error")
    @patch(
        "dagster_dg_cli.dagster_plus_api.graphql_adapter.deployment.DagsterPlusGraphQLClient.from_config"
    )
    def test_list_deployments_json_output(self, mock_client_class, mock_config, snapshot):
        """Test successful deployment list with JSON output."""
        # Setup mocks
        mock_config.return_value = "mock-config"
        mock_client = mock_client_class.return_value
        mock_client.execute.return_value = load_deployment_response_fixture(
            "success_multiple_deployments"
        )

        # Run command with --json flag
        runner = CliRunner()
        result = runner.invoke(list_deployments_command, ["--json"])

        # Verify success
        assert result.exit_code == 0

        # Parse and snapshot the JSON output to avoid formatting differences
        actual_output = json.loads(result.output)
        snapshot.assert_match(actual_output)

    @patch("dagster_dg_cli.cli.api.deployment._get_config_or_error")
    @patch(
        "dagster_dg_cli.dagster_plus_api.graphql_adapter.deployment.DagsterPlusGraphQLClient.from_config"
    )
    def test_list_deployments_api_error(self, mock_client_class, mock_config, snapshot):
        """Test handling of API errors."""
        # Setup mocks
        mock_config.return_value = "mock-config"
        mock_client = mock_client_class.return_value
        mock_client.execute.side_effect = Exception("API Error")

        # Run command
        runner = CliRunner()
        result = runner.invoke(list_deployments_command, [])

        # Verify error handling
        assert result.exit_code != 0

        # Snapshot the error output
        snapshot.assert_match(result.output)

    @patch("dagster_dg_cli.cli.api.deployment._get_config_or_error")
    @patch(
        "dagster_dg_cli.dagster_plus_api.graphql_adapter.deployment.DagsterPlusGraphQLClient.from_config"
    )
    def test_list_deployments_api_error_json_output(self, mock_client_class, mock_config, snapshot):
        """Test handling of API errors with JSON output."""
        # Setup mocks
        mock_config.return_value = "mock-config"
        mock_client = mock_client_class.return_value
        mock_client.execute.side_effect = Exception("API Error")

        # Run command with --json flag
        runner = CliRunner()
        result = runner.invoke(list_deployments_command, ["--json"])

        # Verify error handling
        assert result.exit_code != 0

        # Snapshot the error output
        snapshot.assert_match(result.output)

    @patch("dagster_dg_cli.cli.api.deployment.DagsterPlusCliConfig.exists")
    def test_list_deployments_no_config(self, mock_config_exists, snapshot):
        """Test handling when no Dagster Plus config exists."""
        # Setup mock - no config exists
        mock_config_exists.return_value = False

        # Run command
        runner = CliRunner()
        result = runner.invoke(list_deployments_command, [])

        # Verify error handling
        assert result.exit_code != 0

        # Snapshot the error output
        snapshot.assert_match(result.output)
