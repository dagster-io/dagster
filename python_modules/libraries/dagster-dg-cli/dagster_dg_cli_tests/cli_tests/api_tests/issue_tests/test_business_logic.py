"""Test issue business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

import json

from dagster_dg_cli.cli.api.formatters import format_issue, format_issues
from dagster_rest_resources.schemas.enums import DgApiIssueStatus
from dagster_rest_resources.schemas.issue import (
    DgApiIssue,
    DgApiIssueLinkedAsset,
    DgApiIssueLinkedRun,
    DgApiIssueList,
)


class TestFormatIssues:
    """Test the issue formatting functions."""

    def _create_sample_issue_list(self):
        """Create sample IssueList for testing."""
        issues = [
            DgApiIssue(
                id="1",
                title="Asset materialization failed",
                description="The asset failed to materialize due to a connection error.",
                status=DgApiIssueStatus.OPEN,
                created_by_name="Alice Apple",
                linked_objects=[
                    DgApiIssueLinkedRun(run_id="run-abc-123"),
                    DgApiIssueLinkedAsset(asset_key="my_asset"),
                ],
            ),
            DgApiIssue(
                id="2",
                title="Schedule missed execution",
                description="The daily schedule did not execute as expected.",
                status=DgApiIssueStatus.CLOSED,
                created_by_name="Bob Brown",
                linked_objects=[],
            ),
            DgApiIssue(
                id="3",
                title="Sensor error",
                description="Sensor encountered an unhandled exception.",
                status=DgApiIssueStatus.OPEN,
                created_by_name="Carol Cherry",
                context="Stack trace: ...",
                linked_objects=[],
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
                id="1",
                title="First paginated issue",
                description="Description for first paginated issue.",
                status=DgApiIssueStatus.OPEN,
                created_by_name="Dave Day",
                linked_objects=[],
            ),
        ]
        return DgApiIssueList(items=issues, cursor="1", has_more=True)

    def _create_single_issue(self):
        """Create single Issue for testing."""
        return DgApiIssue(
            id="1",
            title="Critical pipeline failure",
            description="The pipeline failed with a critical error during execution.",
            status=DgApiIssueStatus.OPEN,
            created_by_name="Engineer Engine",
            linked_objects=[
                DgApiIssueLinkedRun(run_id="run-xyz-789"),
                DgApiIssueLinkedAsset(asset_key="namespace/my_critical_asset"),
            ],
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
            id="1",
            title="Minimal issue",
            description="Only required fields.",
            status=DgApiIssueStatus.CLOSED,
            created_by_name="User D'User",
            linked_objects=[],
        )
        result = format_issue(issue, as_json=False)
        snapshot.assert_match(result)

    def test_format_issue_with_run_id_only(self, snapshot):
        """Test formatting issue with run_id but no asset_key or context."""
        issue = DgApiIssue(
            id="1",
            title="Run failure issue",
            description="This issue is linked to a specific run.",
            status=DgApiIssueStatus.OPEN,
            created_by_name="Ops Service Account",
            linked_objects=[DgApiIssueLinkedRun(run_id="run-failing-456")],
        )
        result = format_issue(issue, as_json=False)
        snapshot.assert_match(result)

    def test_format_created_issue_text_output(self, snapshot):
        """Test formatting a newly created issue as text."""
        issue = DgApiIssue(
            id="1",
            title="New pipeline issue",
            description="Pipeline failed unexpectedly.",
            status=DgApiIssueStatus.OPEN,
            created_by_name="Creator Clark",
            linked_objects=[],
        )
        result = format_issue(issue, as_json=False)
        snapshot.assert_match(result)

    def test_format_created_issue_json_output(self, snapshot):
        """Test formatting a newly created issue as JSON."""
        issue = DgApiIssue(
            id="1",
            title="New pipeline issue",
            description="Pipeline failed unexpectedly.",
            status=DgApiIssueStatus.OPEN,
            created_by_name="Creator Clark",
            linked_objects=[],
        )
        result = format_issue(issue, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_updated_issue_text_output(self, snapshot):
        """Test formatting an updated issue as text."""
        issue = DgApiIssue(
            id="1",
            title="Updated issue title",
            description="Updated description after investigation.",
            status=DgApiIssueStatus.CLOSED,
            created_by_name="Owner O'Owner",
            linked_objects=[],
        )
        result = format_issue(issue, as_json=False)
        snapshot.assert_match(result)

    def test_format_updated_issue_json_output(self, snapshot):
        """Test formatting an updated issue as JSON."""
        issue = DgApiIssue(
            id="1",
            title="Updated issue title",
            description="Updated description after investigation.",
            status=DgApiIssueStatus.CLOSED,
            created_by_name="Owner O'Owner",
            linked_objects=[],
        )
        result = format_issue(issue, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_updated_issue_with_context_text_output(self, snapshot):
        """Test formatting an updated issue with context as text."""
        issue = DgApiIssue(
            id="1",
            title="Updated issue title",
            description="Updated description after investigation.",
            status=DgApiIssueStatus.OPEN,
            created_by_name="Owner O'Owner",
            context="New context added during update.",
            linked_objects=[],
        )
        result = format_issue(issue, as_json=False)
        snapshot.assert_match(result)

    def test_format_updated_issue_with_context_json_output(self, snapshot):
        """Test formatting an updated issue with context as JSON."""
        issue = DgApiIssue(
            id="1",
            title="Updated issue title",
            description="Updated description after investigation.",
            status=DgApiIssueStatus.OPEN,
            created_by_name="Owner O'Owner",
            context="New context added during update.",
            linked_objects=[],
        )
        result = format_issue(issue, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)


class TestIssueDataProcessing:
    """Test processing of issue data structures."""

    def test_issue_creation_with_all_statuses(self, snapshot):
        """Test creating issues with all possible status values."""
        issues = [
            DgApiIssue(
                id=str(i + 1),
                title=f"Issue with status {status.value}",
                description=f"Test issue for status {status.value}.",
                status=status,
                created_by_name="Test Tester",
                linked_objects=[],
            )
            for i, status in enumerate(DgApiIssueStatus)
        ]

        issue_list = DgApiIssueList(items=issues, cursor=None, has_more=False)
        result = issue_list.model_dump_json(indent=2)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_issue_list_pagination_fields(self):
        """Test IssueList properly tracks pagination fields."""
        issue = DgApiIssue(
            id="1",
            title="Test",
            description="Test description.",
            status=DgApiIssueStatus.OPEN,
            created_by_name="Test Tester",
            linked_objects=[],
        )
        issue_list = DgApiIssueList(items=[issue], cursor="1", has_more=True)

        assert len(issue_list.items) == 1
        assert issue_list.cursor == "1"
        assert issue_list.has_more is True

    def test_issue_optional_fields_default_to_none(self):
        """Test that optional fields default to None."""
        issue = DgApiIssue(
            id="1",
            title="Test",
            description="Test.",
            status=DgApiIssueStatus.OPEN,
            created_by_name="Test Tester",
            linked_objects=[],
        )

        assert issue.linked_objects == []
        assert issue.context is None
