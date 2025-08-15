"""Integration tests for run view command - testing CLI interface only."""

import json
from unittest.mock import patch

from click.testing import CliRunner
from dagster_dg_cli.cli.plus.api.run.view import view_run_command

from dagster_dg_cli_tests.cli_tests.plus_tests.api_tests.run_tests.fixtures.run_responses import (
    RUN_VIEW_NOT_FOUND_RESPONSE,
    RUN_VIEW_SUCCESS_RESPONSE,
)


class TestViewCommandIntegration:
    """Test the CLI command integration without mocking business logic."""

    def test_successful_command_execution_json(self, dg_plus_cli_config):
        """Test that command executes successfully with valid GraphQL response (JSON output)."""
        # Only mock the GraphQL client - business logic is tested separately
        with patch(
            "dagster_dg_cli.utils.plus.gql_client.DagsterPlusGraphQLClient.from_config"
        ) as mock_client_factory:
            mock_client = mock_client_factory.return_value
            mock_client.execute.return_value = RUN_VIEW_SUCCESS_RESPONSE

            runner = CliRunner()
            result = runner.invoke(view_run_command, ["9d38c7ea", "--json"])

            # Test CLI-level concerns
            assert result.exit_code == 0
            assert result.output.strip()  # Has output

            # Should be valid JSON
            output_data = json.loads(result.output)
            assert output_data["run_id"] == "9d38c7ea"
            assert output_data["status"] == "SUCCESS"

            # Verify GraphQL query was called correctly
            mock_client.execute.assert_called_once()
            call_args = mock_client.execute.call_args
            assert "CliRunQuery" in call_args[0][0]  # Query contains expected name
            assert call_args[0][1] == {"runId": "9d38c7ea"}  # Correct variables

    def test_successful_command_execution_human_readable(self, dg_plus_cli_config):
        """Test that command executes successfully with human-readable output."""
        with patch(
            "dagster_dg_cli.utils.plus.gql_client.DagsterPlusGraphQLClient.from_config"
        ) as mock_client_factory:
            mock_client = mock_client_factory.return_value
            mock_client.execute.return_value = RUN_VIEW_SUCCESS_RESPONSE

            runner = CliRunner()
            result = runner.invoke(view_run_command, ["9d38c7ea"])

            assert result.exit_code == 0
            # Check that human-readable format contains expected fields
            assert "run_id: 9d38c7ea" in result.output
            assert "status: SUCCESS" in result.output

    def test_run_not_found_error_handling(self, dg_plus_cli_config):
        """Test error handling for run not found."""
        with patch(
            "dagster_dg_cli.utils.plus.gql_client.DagsterPlusGraphQLClient.from_config"
        ) as mock_client_factory:
            mock_client = mock_client_factory.return_value
            mock_client.execute.return_value = RUN_VIEW_NOT_FOUND_RESPONSE

            runner = CliRunner()
            result = runner.invoke(view_run_command, ["nonexistent"])

            # Should have non-zero exit code
            assert result.exit_code != 0
            # Should show error message
            assert "Run not found" in result.output

    def test_recording_flag_integration(self, dg_plus_cli_config):
        """Test that --record flag is properly handled."""
        with patch(
            "dagster_dg_cli.utils.plus.gql_client.DagsterPlusGraphQLClient.from_config"
        ) as mock_client_factory:
            with patch(
                "dagster_dg_cli.cli.plus.api.run.recording.record_graphql_interaction"
            ) as mock_record:
                mock_client = mock_client_factory.return_value
                mock_client.execute.return_value = RUN_VIEW_SUCCESS_RESPONSE

                runner = CliRunner()
                result = runner.invoke(view_run_command, ["9d38c7ea", "--record"])

                assert result.exit_code == 0
                # Verify recording was called
                mock_record.assert_called_once()
                # Check recording was called with correct parameters
                call_args = mock_record.call_args[1]  # kwargs
                assert "run_view" in call_args.values()

    def test_recording_flag_not_called_by_default(self, dg_plus_cli_config):
        """Test that recording is not called when --record flag is not used."""
        with patch(
            "dagster_dg_cli.utils.plus.gql_client.DagsterPlusGraphQLClient.from_config"
        ) as mock_client_factory:
            with patch(
                "dagster_dg_cli.cli.plus.api.run.recording.record_graphql_interaction"
            ) as mock_record:
                mock_client = mock_client_factory.return_value
                mock_client.execute.return_value = RUN_VIEW_SUCCESS_RESPONSE

                runner = CliRunner()
                result = runner.invoke(view_run_command, ["9d38c7ea"])

                assert result.exit_code == 0
                # Verify recording was NOT called
                mock_record.assert_not_called()

    def test_unexpected_exception_handling(self, dg_plus_cli_config):
        """Test handling of unexpected exceptions."""
        with patch(
            "dagster_dg_cli.utils.plus.gql_client.DagsterPlusGraphQLClient.from_config"
        ) as mock_client_factory:
            mock_client = mock_client_factory.return_value
            mock_client.execute.side_effect = Exception("Network error")

            runner = CliRunner()

            # Test JSON error format
            result = runner.invoke(view_run_command, ["9d38c7ea", "--json"])
            assert result.exit_code != 0
            # Should contain error in stderr for JSON format

            # Test human-readable error format
            result = runner.invoke(view_run_command, ["9d38c7ea"])
            assert result.exit_code != 0
            assert "Error querying Dagster Plus API" in result.output
