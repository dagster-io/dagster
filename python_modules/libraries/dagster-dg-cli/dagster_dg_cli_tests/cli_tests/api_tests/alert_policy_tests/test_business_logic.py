"""Test alert policy business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

import json

from dagster_dg_cli.cli.api.formatters import format_alert_policies, format_alert_policy_sync_result
from dagster_rest_resources.graphql_adapter.alert_policy import (
    process_alert_policies_response,
    process_reconcile_response,
)

from dagster_dg_cli_tests.cli_tests.api_tests.test_dynamic_command_execution import (
    load_recorded_graphql_responses,
)


class TestFormatAlertPolicies:
    """Test the alert policy formatting functions."""

    def test_format_policies_text_output(self, snapshot):
        """Test formatting alert policies as YAML text."""
        response = load_recorded_graphql_responses("alert_policy", "success_list_policies")[0]
        policies = process_alert_policies_response(response)
        result = format_alert_policies(policies, as_json=False)
        snapshot.assert_match(result)

    def test_format_policies_json_output(self, snapshot):
        """Test formatting alert policies as JSON."""
        response = load_recorded_graphql_responses("alert_policy", "success_list_policies")[0]
        policies = process_alert_policies_response(response)
        result = format_alert_policies(policies, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)


class TestFormatAlertPolicySyncResult:
    """Test the alert policy sync result formatting."""

    def test_format_sync_result_text(self, snapshot):
        """Test formatting sync result as text."""
        response = load_recorded_graphql_responses("alert_policy", "success_reconcile_policies")[0]
        result = process_reconcile_response(response)
        output = format_alert_policy_sync_result(result, as_json=False)
        snapshot.assert_match(output)

    def test_format_sync_result_json(self, snapshot):
        """Test formatting sync result as JSON."""
        response = load_recorded_graphql_responses("alert_policy", "success_reconcile_policies")[0]
        result = process_reconcile_response(response)
        output = format_alert_policy_sync_result(result, as_json=True)
        parsed = json.loads(output)
        snapshot.assert_match(parsed)
