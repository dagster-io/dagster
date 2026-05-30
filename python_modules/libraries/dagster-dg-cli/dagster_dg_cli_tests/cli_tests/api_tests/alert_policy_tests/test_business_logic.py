"""Test alert policy business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

import json

from dagster_dg_cli.cli.api.formatters import format_alert_policies, format_alert_policy_sync_result
from dagster_rest_resources.schemas.alert_policy import (
    DgApiAlertPolicyDocument,
    DgApiAlertPolicySyncResult,
)


class TestFormatDgAlertPolicies:
    """Test the alert policy formatting functions."""

    def _create_sample_alert_policies(self) -> DgApiAlertPolicyDocument:
        return DgApiAlertPolicyDocument(
            items=[
                {
                    "name": "email-on-failure",
                    "description": "Send email on job failure",
                    "event_types": ["JOB_FAILURE"],
                    "notification_service": {"email": {"email_addresses": ["team@example.com"]}},
                    "tags": [],
                },
                {
                    "name": "slack-on-sla-miss",
                    "description": "Notify Slack on SLA miss",
                    "event_types": ["ASSET_OVERDUE"],
                    "notification_service": {
                        "slack": {
                            "slack_workspace_name": "dagster",
                            "slack_channel_name": "#alerts",
                        }
                    },
                    "tags": [{"key": "team", "value": "data-eng"}],
                },
            ]
        )

    def test_format_policies_text_output(self, snapshot):
        """Test formatting alert policies as YAML text."""
        policies = self._create_sample_alert_policies()
        result = format_alert_policies(policies, as_json=False)
        snapshot.assert_match(result)

    def test_format_policies_json_output(self, snapshot):
        """Test formatting alert policies as JSON."""
        policies = self._create_sample_alert_policies()
        result = format_alert_policies(policies, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)


class TestFormatDgApiAlertPolicySyncResult:
    """Test the alert policy sync result formatting."""

    def _create_sample_alert_policy_sync_result(self) -> DgApiAlertPolicySyncResult:
        return DgApiAlertPolicySyncResult(
            items=["email-on-failure", "slack-on-sla-miss"],
        )

    def test_format_sync_result_text(self, snapshot):
        """Test formatting sync result as text."""
        sync_result = self._create_sample_alert_policy_sync_result()
        output = format_alert_policy_sync_result(sync_result, as_json=False)
        snapshot.assert_match(output)

    def test_format_sync_result_json(self, snapshot):
        """Test formatting sync result as JSON."""
        sync_result = self._create_sample_alert_policy_sync_result()
        output = format_alert_policy_sync_result(sync_result, as_json=True)
        parsed = json.loads(output)
        snapshot.assert_match(parsed)
