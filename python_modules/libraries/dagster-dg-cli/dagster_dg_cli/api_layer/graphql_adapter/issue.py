"""GraphQL adapter for issue operations."""

from typing import Any

from dagster_dg_cli.api_layer.schemas.issue import DgApiIssue, DgApiIssueList, DgApiIssueStatus
from dagster_dg_cli.utils.plus.gql_client import IGraphQLClient

GET_ISSUE_WITH_CONTEXT_QUERY = """
query FetchIssue($issueId: String!) {
    issue(issueId: $issueId) {
        ... on Issue {
            __typename
            id
            title
            description
            status
            context
            origin {
                ... on Run {
                    __typename
                    id
                }
                ... on Asset {
                    __typename
                    key {
                        path
                    }
                }
            }
            createdBy {
                email
            }
        }
        ... on UnauthorizedError {
            __typename
            message
        }
        ... on PythonError {
            __typename
            message
        }
    }
}
"""

LIST_ISSUES_QUERY = """
query FetchIssues($limit: Int!, $cursor: String) {
    issues(limit: $limit, cursor: $cursor) {
        ... on IssueConnection {
            __typename
            issues {
                id
                title
                status
                createdBy {
                    email
                }
            }
            cursor
            hasMore
        }
        ... on UnauthorizedError {
            __typename
            message
        }
        ... on PythonError {
            __typename
            message
        }
    }
}
"""


def get_issue_via_graphql(client: IGraphQLClient, issue_id: str) -> DgApiIssue:
    """Get a single issue via GraphQL."""
    result = client.execute(GET_ISSUE_WITH_CONTEXT_QUERY, variables={"issueId": issue_id})
    issue = result["issue"]

    typename = issue.get("__typename")
    if typename in ("UnauthorizedError", "PythonError"):
        raise Exception(issue["message"])
    if typename != "Issue":
        raise Exception(f"Issue not found: {issue_id}")

    context = issue.get("context")
    run_id = None
    asset_key = None
    origin = issue.get("origin")
    if origin:
        if origin.get("__typename") == "Run":
            run_id = origin["id"]
        elif origin.get("__typename") == "Asset":
            asset_key = origin["key"]["path"]

    return DgApiIssue(
        id=issue["id"],
        title=issue["title"],
        description=issue["description"],
        status=DgApiIssueStatus(issue["status"]),
        created_by_email=issue["createdBy"]["email"],
        run_id=run_id,
        asset_key=asset_key,
        context=context,
    )


def list_issues_via_graphql(
    client: IGraphQLClient,
    limit: int = 10,
    cursor: str | None = None,
) -> DgApiIssueList:
    """List issues via GraphQL with pagination."""
    variables: dict[str, Any] = {"limit": limit}
    if cursor:
        variables["cursor"] = cursor

    result = client.execute(LIST_ISSUES_QUERY, variables=variables)
    issues_result = result["issues"]

    typename = issues_result.get("__typename")
    if typename in ("UnauthorizedError", "PythonError"):
        raise Exception(issues_result["message"])
    if typename != "IssueConnection":
        raise Exception(f"Unexpected response type: {typename}")

    items = []
    for issue_data in issues_result.get("issues", []):
        items.append(
            DgApiIssue(
                id=issue_data["id"],
                title=issue_data["title"],
                description="",
                status=DgApiIssueStatus(issue_data["status"]),
                created_by_email=issue_data["createdBy"]["email"],
            )
        )

    return DgApiIssueList(
        items=items,
        cursor=issues_result.get("cursor"),
        has_more=issues_result.get("hasMore", False),
    )
