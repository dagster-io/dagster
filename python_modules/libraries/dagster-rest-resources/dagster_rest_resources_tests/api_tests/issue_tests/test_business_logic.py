"""Test issue business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

import json

from dagster_rest_resources.schemas.issue import DgApiIssue, DgApiIssueList, DgApiIssueStatus


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
