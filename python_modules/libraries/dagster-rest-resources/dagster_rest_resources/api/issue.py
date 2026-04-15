"""Issue API implementation."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.graphql_adapter.issue import (
    create_issue_via_graphql,
    get_issue_via_graphql,
    list_issues_via_graphql,
    update_issue_via_graphql,
)

if TYPE_CHECKING:
    from dagster_rest_resources.schemas.issue import DgApiIssue, DgApiIssueList, DgApiIssueStatus


@dataclass(frozen=True)
class DgApiIssueApi:
    """API for issue operations."""

    client: IGraphQLClient

    def get_issue(self, issue_id: str) -> "DgApiIssue":
        """Get an issue by ID."""
        return get_issue_via_graphql(self.client, issue_id)

    def list_issues(
        self,
        limit: int = 10,
        cursor: str | None = None,
        statuses: list[str] | None = None,
        created_after: float | None = None,
        created_before: float | None = None,
    ) -> "DgApiIssueList":
        """List issues with pagination and filtering."""
        return list_issues_via_graphql(
            self.client,
            limit=limit,
            cursor=cursor,
            statuses=statuses,
            created_after=created_after,
            created_before=created_before,
        )

    def create_issue(self, title: str, description: str) -> "DgApiIssue":
        """Create a new issue."""
        return create_issue_via_graphql(self.client, title=title, description=description)

    def update_issue(
        self,
        issue_id: str,
        status: "DgApiIssueStatus | None" = None,
        title: str | None = None,
        description: str | None = None,
        context: str | None = None,
    ) -> "DgApiIssue":
        """Update an existing issue."""
        return update_issue_via_graphql(
            self.client,
            issue_id=issue_id,
            status=status,
            title=title,
            description=description,
            context=context,
        )
