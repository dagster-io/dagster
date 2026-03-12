"""Test issue business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

import json

from dagster_dg_cli.api_layer.schemas.issue import DgApiIssue, DgApiIssueList, DgApiIssueStatus
from dagster_dg_cli.cli.api.formatters import format_issue, format_issues


class TestFormatIssues:
    """Test the issue formatting functions."""

    def _create_sample_issue_list(self):
        """Create sample IssueList for testing."""
        issues = [
            DgApiIssue(
                id="issue-1-uuid-12345",
                title="Asset materialization failed",
                description="The asset failed to materialize due to a connection error.",
                status=DgApiIssueStatus.OPEN,
                created_by_email="alice@example.com",
                run_id="run-abc-123",
                asset_key=["my_asset"],
            ),
            DgApiIssue(
                id="issue-2-uuid-67890",
                title="Schedule missed execution",
                description="The daily schedule did not execute as expected.",
                status=DgApiIssueStatus.CLOSED,
                created_by_email="bob@example.com",
            ),
            DgApiIssue(
                id="issue-3-uuid-abcdef",
                title="Sensor error",
                description="Sensor encountered an unhandled exception.",
                status=DgApiIssueStatus.OPEN,
                created_by_email="carol@example.com",
                context="Stack trace: ...",
            ),
        ]
        return DgApiIssueList(items=issues, cursor=None, has_more=False)

    def _create_empty_issue_list(self):
        """Create empty IssueList for testing."""
        return DgApiIssueList(items=[], cursor=None, has_more=False)

    def _create_paginated_issue_list(self):
        """Create IssueList with pagination cursor for testing."""
        issues = [
            DgApiIssue(
                id="issue-page-1-uuid",
                title="First paginated issue",
                description="Description for first paginated issue.",
                status=DgApiIssueStatus.OPEN,
                created_by_email="dave@example.com",
            ),
        ]
        return DgApiIssueList(items=issues, cursor="next-page-cursor-xyz", has_more=True)

    def _create_single_issue(self):
        """Create single Issue for testing."""
        return DgApiIssue(
            id="single-issue-uuid-xyz",
            title="Critical pipeline failure",
            description="The pipeline failed with a critical error during execution.",
            status=DgApiIssueStatus.OPEN,
            created_by_email="engineer@example.com",
            run_id="run-xyz-789",
            asset_key=["namespace", "my_critical_asset"],
            context="Additional diagnostic information here.",
        )

    def test_format_issues_text_output(self, snapshot):
        """Test formatting issues list as text."""
        issue_list = self._create_sample_issue_list()
        result = format_issues(issue_list, as_json=False)
        snapshot.assert_match(result)

    def test_format_issues_json_output(self, snapshot):
        """Test formatting issues list as JSON."""
        issue_list = self._create_sample_issue_list()
        result = format_issues(issue_list, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_empty_issues_text_output(self, snapshot):
        """Test formatting empty issue list as text."""
        issue_list = self._create_empty_issue_list()
        result = format_issues(issue_list, as_json=False)
        snapshot.assert_match(result)

    def test_format_empty_issues_json_output(self, snapshot):
        """Test formatting empty issue list as JSON."""
        issue_list = self._create_empty_issue_list()
        result = format_issues(issue_list, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_paginated_issues_text_output(self, snapshot):
        """Test formatting paginated issue list includes pagination note."""
        issue_list = self._create_paginated_issue_list()
        result = format_issues(issue_list, as_json=False)
        snapshot.assert_match(result)

    def test_format_paginated_issues_json_output(self, snapshot):
        """Test formatting paginated issue list as JSON includes cursor."""
        issue_list = self._create_paginated_issue_list()
        result = format_issues(issue_list, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_single_issue_text_output(self, snapshot):
        """Test formatting single issue as text."""
        issue = self._create_single_issue()
        result = format_issue(issue, as_json=False)
        snapshot.assert_match(result)

    def test_format_single_issue_json_output(self, snapshot):
        """Test formatting single issue as JSON."""
        issue = self._create_single_issue()
        result = format_issue(issue, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_issue_minimal_fields(self, snapshot):
        """Test formatting issue with only required fields (no optional fields)."""
        issue = DgApiIssue(
            id="minimal-issue-uuid",
            title="Minimal issue",
            description="Only required fields.",
            status=DgApiIssueStatus.CLOSED,
            created_by_email="user@example.com",
        )
        result = format_issue(issue, as_json=False)
        snapshot.assert_match(result)

    def test_format_issue_with_run_id_only(self, snapshot):
        """Test formatting issue with run_id but no asset_key or context."""
        issue = DgApiIssue(
            id="run-only-issue-uuid",
            title="Run failure issue",
            description="This issue is linked to a specific run.",
            status=DgApiIssueStatus.OPEN,
            created_by_email="ops@example.com",
            run_id="run-failing-456",
        )
        result = format_issue(issue, as_json=False)
        snapshot.assert_match(result)


class TestIssueDataProcessing:
    """Test processing of issue data structures."""

    def test_issue_creation_with_all_statuses(self, snapshot):
        """Test creating issues with all possible status values."""
        issues = [
            DgApiIssue(
                id=f"issue-{status.value.lower()}-uuid",
                title=f"Issue with status {status.value}",
                description=f"Test issue for status {status.value}.",
                status=status,
                created_by_email="test@example.com",
            )
            for status in DgApiIssueStatus
        ]

        issue_list = DgApiIssueList(items=issues, cursor=None, has_more=False)
        result = issue_list.model_dump_json(indent=2)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_issue_list_pagination_fields(self):
        """Test IssueList properly tracks pagination fields."""
        issue = DgApiIssue(
            id="test-issue",
            title="Test",
            description="Test description.",
            status=DgApiIssueStatus.OPEN,
            created_by_email="test@example.com",
        )
        issue_list = DgApiIssueList(items=[issue], cursor="abc123", has_more=True)

        assert len(issue_list.items) == 1
        assert issue_list.cursor == "abc123"
        assert issue_list.has_more is True

    def test_issue_optional_fields_default_to_none(self):
        """Test that optional fields default to None."""
        issue = DgApiIssue(
            id="test-issue",
            title="Test",
            description="Test.",
            status=DgApiIssueStatus.OPEN,
            created_by_email="test@example.com",
        )

        assert issue.run_id is None
        assert issue.asset_key is None
        assert issue.context is None
