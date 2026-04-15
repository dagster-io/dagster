"""GraphQL adapter for issue operations."""

from typing import Any

from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.issue import DgApiIssue, DgApiIssueList, DgApiIssueStatus

CREATE_ISSUE_MUTATION = """
mutation CliCreateIssueMutation($title: String!, $description: String!, $chatId: Int) {
    createIssue(title: $title, description: $description, chatId: $chatId) {
        ... on CreateIssueSuccess {
            __typename
            issue {
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

UPDATE_ISSUE_MUTATION = """
mutation CliUpdateIssueMutation($issueId: String!, $status: IssueStatus, $title: String, $description: String, $context: String) {
    updateIssue(issueId: $issueId, status: $status, title: $title, description: $description, context: $context) {
        ... on UpdateIssueSuccess {
            __typename
            issue {
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
query FetchIssues($limit: Int!, $cursor: String, $filters: IssuesFilter) {
    issues(limit: $limit, cursor: $cursor, filters: $filters) {
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

    return _parse_issue_from_graphql(issue)


def list_issues_via_graphql(
    client: IGraphQLClient,
    limit: int = 10,
    cursor: str | None = None,
    statuses: list[str] | None = None,
    created_after: float | None = None,
    created_before: float | None = None,
) -> DgApiIssueList:
    """List issues via GraphQL with pagination and filtering."""
    variables: dict[str, Any] = {"limit": limit}
    if cursor:
        variables["cursor"] = cursor

    filters: dict[str, Any] = {}
    if statuses:
        filters["statuses"] = statuses
    if created_after is not None:
        filters["createdAfter"] = created_after
    if created_before is not None:
        filters["createdBefore"] = created_before
    if filters:
        variables["filters"] = filters

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


def _parse_issue_from_graphql(issue: dict[str, Any]) -> DgApiIssue:
    """Parse an issue dict from a GraphQL response into a DgApiIssue."""
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


def create_issue_via_graphql(
    client: IGraphQLClient,
    title: str,
    description: str,
) -> DgApiIssue:
    """Create a new issue via GraphQL."""
    variables: dict[str, Any] = {"title": title, "description": description, "chatId": None}
    result = client.execute(CREATE_ISSUE_MUTATION, variables=variables)
    create_result = result["createIssue"]

    typename = create_result.get("__typename")
    if typename in ("UnauthorizedError", "PythonError"):
        raise Exception(create_result["message"])
    if typename != "CreateIssueSuccess":
        raise Exception(f"Unexpected response type: {typename}")

    return _parse_issue_from_graphql(create_result["issue"])


def update_issue_via_graphql(
    client: IGraphQLClient,
    issue_id: str,
    status: DgApiIssueStatus | None = None,
    title: str | None = None,
    description: str | None = None,
    context: str | None = None,
) -> DgApiIssue:
    """Update an existing issue via GraphQL."""
    variables: dict[str, Any] = {"issueId": issue_id}
    if status is not None:
        variables["status"] = status.value
    if title is not None:
        variables["title"] = title
    if description is not None:
        variables["description"] = description
    if context is not None:
        variables["context"] = context

    result = client.execute(UPDATE_ISSUE_MUTATION, variables=variables)
    update_result = result["updateIssue"]

    typename = update_result.get("__typename")
    if typename in ("UnauthorizedError", "PythonError"):
        raise Exception(update_result["message"])
    if typename != "UpdateIssueSuccess":
        raise Exception(f"Unexpected response type: {typename}")

    return _parse_issue_from_graphql(update_result["issue"])
