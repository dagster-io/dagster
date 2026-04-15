"""Test deployment business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

import json

from dagster_dg_cli.cli.api.formatters import format_deployment_settings, format_deployments
from dagster_rest_resources.graphql_adapter.deployment import process_deployment_settings_response
from dagster_rest_resources.schemas.deployment import Deployment, DeploymentList, DeploymentType

from dagster_dg_cli_tests.cli_tests.api_tests.test_dynamic_command_execution import (
    load_recorded_graphql_responses,
)


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
