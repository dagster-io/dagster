"""Test deployment business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

import pytest
from dagster_rest_resources.api.deployments import DgApiDeploymentApi
from dagster_rest_resources.graphql_adapter.deployment import (
    process_branch_deployments_response,
    process_delete_deployment_response,
    process_deployment_settings_response,
    process_deployments_response,
    process_set_deployment_settings_response,
)
from dagster_rest_resources.schemas.deployment import DeploymentType

from dagster_rest_resources_tests.api_tests.test_dynamic_command_execution import (
    ReplayClient,
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


class TestProcessBranchDeploymentsResponse:
    """Test the pure function that processes branch deployments GraphQL responses."""

    def test_successful_response_processing(self, snapshot):
        """Test processing a successful branch deployments response."""
        response = load_recorded_graphql_responses("deployment", "success_branch_deployments")[0]
        branch_data = response.get("branchDeployments", {})
        result = process_branch_deployments_response(branch_data)

        snapshot.assert_match(result)

    def test_empty_nodes(self, snapshot):
        """Test processing a response with empty nodes list."""
        result = process_branch_deployments_response({"nodes": []})

        snapshot.assert_match(result)

    def test_missing_nodes_key(self, snapshot):
        """Test processing a response missing the nodes key."""
        result = process_branch_deployments_response({})

        snapshot.assert_match(result)


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


class TestProcessDeleteDeploymentResponse:
    """Test the pure function that processes delete deployment GraphQL responses."""

    def test_successful_branch_delete(self, snapshot):
        """Test processing a successful delete branch deployment response."""
        response = load_recorded_graphql_responses(
            "deployment", "success_delete_branch_deployment"
        )[0]
        deployment_data = response.get("deleteDeployment", {})
        result = process_delete_deployment_response(deployment_data)

        snapshot.assert_match(result)

    def test_successful_production_delete(self, snapshot):
        """Test processing a successful delete production deployment response."""
        response = load_recorded_graphql_responses(
            "deployment", "success_delete_production_deployment"
        )[0]
        deployment_data = response.get("deleteDeployment", {})
        result = process_delete_deployment_response(deployment_data)

        snapshot.assert_match(result)


class TestDeleteDeploymentSafetyCheck:
    """Test the safety check logic for deleting deployments."""

    def test_branch_deployment_succeeds_without_flag(self):
        """Deleting a BRANCH deployment should not require the safety flag."""
        # First response: get_deployment (resolve name to ID)
        # Second response: delete_deployment mutation
        get_response = {
            "deploymentByName": {
                "__typename": "DagsterCloudDeployment",
                "deploymentId": 300001,
                "deploymentName": "feature-add-auth",
                "deploymentType": "BRANCH",
            }
        }
        delete_response = {
            "deleteDeployment": {
                "__typename": "DagsterCloudDeployment",
                "deploymentId": 300001,
                "deploymentName": "feature-add-auth",
                "deploymentType": "BRANCH",
            }
        }
        client = ReplayClient([get_response, delete_response])
        api = DgApiDeploymentApi(client)

        result = api.delete_deployment("feature-add-auth")
        assert result.name == "feature-add-auth"
        assert result.type == DeploymentType.BRANCH

    def test_production_deployment_fails_without_flag(self):
        """Deleting a PRODUCTION deployment without --allow-delete-full-deployment should fail."""
        get_response = {
            "deploymentByName": {
                "__typename": "DagsterCloudDeployment",
                "deploymentId": 1,
                "deploymentName": "prod",
                "deploymentType": "PRODUCTION",
            }
        }
        client = ReplayClient([get_response])
        api = DgApiDeploymentApi(client)

        with pytest.raises(ValueError, match="production deployment"):
            api.delete_deployment("prod")

    def test_production_deployment_succeeds_with_flag(self):
        """Deleting a PRODUCTION deployment with allow_full_deployment=True should succeed."""
        get_response = {
            "deploymentByName": {
                "__typename": "DagsterCloudDeployment",
                "deploymentId": 1,
                "deploymentName": "prod",
                "deploymentType": "PRODUCTION",
            }
        }
        delete_response = {
            "deleteDeployment": {
                "__typename": "DagsterCloudDeployment",
                "deploymentId": 1,
                "deploymentName": "prod",
                "deploymentType": "PRODUCTION",
            }
        }
        client = ReplayClient([get_response, delete_response])
        api = DgApiDeploymentApi(client)

        result = api.delete_deployment("prod", allow_full_deployment=True)
        assert result.name == "prod"
        assert result.type == DeploymentType.PRODUCTION
