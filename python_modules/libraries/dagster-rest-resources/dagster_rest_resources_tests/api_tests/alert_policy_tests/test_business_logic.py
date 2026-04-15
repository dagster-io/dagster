"""Test alert policy business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

import pytest
from dagster_rest_resources.graphql_adapter.alert_policy import (
    process_alert_policies_response,
    process_reconcile_response,
)

from dagster_rest_resources_tests.api_tests.test_dynamic_command_execution import (
    load_recorded_graphql_responses,
)


class TestProcessAlertPoliciesResponse:
    """Test the pure function that processes GraphQL responses for alert policies."""

    def test_successful_response_processing(self, snapshot):
        """Test processing a successful GraphQL response."""
        response = load_recorded_graphql_responses("alert_policy", "success_list_policies")[0]
        result = process_alert_policies_response(response)

        snapshot.assert_match(result)

    def test_python_error_response(self):
        """Test processing a PythonError response."""
        response = {
            "alertPoliciesAsDocumentOrError": {
                "__typename": "PythonError",
                "message": "Something went wrong",
            }
        }
        with pytest.raises(ValueError, match="Error fetching alert policies"):
            process_alert_policies_response(response)

    def test_unauthorized_error_response(self):
        """Test processing an UnauthorizedError response."""
        response = {
            "alertPoliciesAsDocumentOrError": {
                "__typename": "UnauthorizedError",
                "message": "Not authorized",
            }
        }
        with pytest.raises(ValueError, match="Error fetching alert policies"):
            process_alert_policies_response(response)


class TestProcessReconcileResponse:
    """Test the pure function that processes reconcile mutation responses."""

    def test_successful_reconcile(self, snapshot):
        """Test processing a successful reconcile response."""
        response = load_recorded_graphql_responses("alert_policy", "success_reconcile_policies")[0]
        result = process_reconcile_response(response)

        snapshot.assert_match(result)

    def test_unauthorized_error(self):
        """Test processing an unauthorized error from reconcile."""
        response = {
            "reconcileAlertPoliciesFromDocument": {
                "__typename": "UnauthorizedError",
                "message": "Not authorized",
            }
        }
        with pytest.raises(ValueError, match="Error reconciling alert policies"):
            process_reconcile_response(response)

    def test_invalid_alert_policy_error(self):
        """Test processing an invalid alert policy error."""
        response = {
            "reconcileAlertPoliciesFromDocument": {
                "__typename": "InvalidAlertPolicyError",
                "message": "Invalid policy configuration",
            }
        }
        with pytest.raises(ValueError, match="Error reconciling alert policies"):
            process_reconcile_response(response)
