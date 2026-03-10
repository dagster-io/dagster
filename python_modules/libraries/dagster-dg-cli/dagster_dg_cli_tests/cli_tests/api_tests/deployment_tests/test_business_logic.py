"""Test deployment business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

import json

import pytest
from dagster_dg_cli.api_layer.graphql_adapter.deployment import (
    process_deployment_settings_response,
    process_deployments_response,
    process_set_deployment_settings_response,
)
from dagster_dg_cli.api_layer.schemas.deployment import Deployment, DeploymentList, DeploymentType
from dagster_dg_cli.cli.api.formatters import format_deployment_settings, format_deployments

from dagster_dg_cli_tests.cli_tests.api_tests.test_dynamic_command_execution import (
    load_recorded_graphql_responses,
)


class TestProcessDeploymentsResponse:
    """Test the pure function that processes GraphQL responses."""

    def test_successful_response_processing(self, snapshot):
        """Test processing a successful GraphQL response."""
        response = load_recorded_graphql_responses("deployment", "success_multiple_deployments")[0]
        result = process_deployments_response(response)

        # Snapshot the entire result to capture structure and data
        snapshot.assert_match(result)

    def test_response_processing_with_limit(self, snapshot):
        """Test response processing with a limit applied."""
        response = load_recorded_graphql_responses("deployment", "success_multiple_deployments")[0]
        result = process_deployments_response(response)

        # Snapshot the full result (limit functionality moved to higher level)
        snapshot.assert_match(result)

    def test_empty_response_processing(self, snapshot):
        """Test processing an empty GraphQL response."""
        response = load_recorded_graphql_responses("deployment", "empty_deployments")[0]
        result = process_deployments_response(response)

        # Snapshot empty result
        snapshot.assert_match(result)

    def test_missing_full_deployments_key(self, snapshot):
        """Test processing a response missing the fullDeployments key."""
        malformed_response = {}
        result = process_deployments_response(malformed_response)

        # Snapshot result when key is missing
        snapshot.assert_match(result)


class TestFormatDeployments:
    """Test the deployment formatting functions."""

    def _create_sample_deployment_list(self):
        """Create sample DeploymentList from fixture data."""
        # Load from fixture and convert to domain objects
        response = load_recorded_graphql_responses("deployment", "success_multiple_deployments")[0]
        deployments = [
            Deployment(
                id=dep["deploymentId"],
                name=dep["deploymentName"],
                type=DeploymentType(dep["deploymentType"]),
            )
            for dep in response["fullDeployments"]
        ]
        return DeploymentList(items=deployments, total=len(deployments))

    def test_format_deployments_text_output(self, snapshot):
        """Test formatting deployments as text."""
        deployment_list = self._create_sample_deployment_list()
        result = format_deployments(deployment_list, as_json=False)

        # Snapshot the entire text output
        snapshot.assert_match(result)

    def test_format_deployments_json_output(self, snapshot):
        """Test formatting deployments as JSON."""
        deployment_list = self._create_sample_deployment_list()
        result = format_deployments(deployment_list, as_json=True)

        # For JSON, we want to snapshot the parsed structure to avoid formatting differences
        parsed = json.loads(result)
        snapshot.assert_match(parsed)


class TestProcessDeploymentSettingsResponse:
    """Test the pure functions that process deployment settings GraphQL responses."""

    def test_successful_get_settings(self, snapshot):
        """Test processing a successful get deployment settings response."""
        response = load_recorded_graphql_responses("deployment", "success_get_settings")[0]
        result = process_deployment_settings_response(response)
        snapshot.assert_match(result)

    def test_successful_set_settings(self, snapshot):
        """Test processing a successful set deployment settings response."""
        response = load_recorded_graphql_responses("deployment", "success_set_settings")[0]
        result = process_set_deployment_settings_response(response)
        snapshot.assert_match(result)

    def test_set_settings_unauthorized_error(self):
        """Test processing an unauthorized error from set deployment settings."""
        response = {"__typename": "UnauthorizedError", "message": "Not authorized"}
        with pytest.raises(ValueError, match="Error setting deployment settings"):
            process_set_deployment_settings_response(response)

    def test_set_settings_python_error(self):
        """Test processing a Python error from set deployment settings."""
        response = {"__typename": "PythonError", "message": "Something went wrong"}
        with pytest.raises(ValueError, match="Error setting deployment settings"):
            process_set_deployment_settings_response(response)


class TestFormatDeploymentSettings:
    """Test the deployment settings formatting functions."""

    def test_format_settings_text_output(self, snapshot):
        """Test formatting deployment settings as YAML text."""
        response = load_recorded_graphql_responses("deployment", "success_get_settings")[0]
        settings = process_deployment_settings_response(response)
        result = format_deployment_settings(settings, as_json=False)
        snapshot.assert_match(result)

    def test_format_settings_json_output(self, snapshot):
        """Test formatting deployment settings as JSON."""
        response = load_recorded_graphql_responses("deployment", "success_get_settings")[0]
        settings = process_deployment_settings_response(response)
        result = format_deployment_settings(settings, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)
