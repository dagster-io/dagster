from dataclasses import dataclass

from typing_extensions import assert_never

from dagster_rest_resources.__generated__.enums import IssueStatus
from dagster_rest_resources.__generated__.fragments import IssueFields
from dagster_rest_resources.__generated__.input_types import (
    AssetKeyInput,
    IssueLinkedObjectInput,
    IssuesFilter,
)
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.exception import (
    DagsterPlusGraphqlError,
    DagsterPlusUnauthorizedError,
)
from dagster_rest_resources.schemas.issue import (
    DgApiIssue,
    DgApiIssueLinkedAsset,
    DgApiIssueLinkedRun,
    DgApiIssueList,
)


@dataclass(frozen=True)
class DgApiIssueApi:
    _client: IGraphQLClient

    def get_issue(self, issue_id: str) -> DgApiIssue:
        result = self._client.get_issue(issue_id=issue_id).issue
        if result is None:
            raise DagsterPlusGraphqlError(f"Issue not found: {issue_id}")

        match result.typename__:
            case "Issue":
                return self._build_issue(result)  # ty: ignore[invalid-argument-type]
            case "UnauthorizedError":
                raise DagsterPlusUnauthorizedError(f"Error fetching issue: {result.message}")  # ty: ignore[unresolved-attribute]
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error fetching issue: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def list_issues(
        self,
        limit: int = 10,
        cursor: str | None = None,
        statuses: list[IssueStatus] | None = None,
        created_after: float | None = None,
        created_before: float | None = None,
    ) -> DgApiIssueList:
        filters: IssuesFilter | None = None
        if statuses is not None or created_after is not None or created_before is not None:
            filters = IssuesFilter(
                statuses=statuses,
                createdAfter=created_after,
                createdBefore=created_before,
            )

        result = self._client.list_issues(limit=limit, cursor=cursor, filters=filters).issues
        if result is None:
            return DgApiIssueList(items=[], cursor=None, has_more=False)

        match result.typename__:
            case "IssueConnection":
                return DgApiIssueList(
                    items=[self._build_issue(i) for i in result.issues],  # ty: ignore[unresolved-attribute]
                    cursor=result.cursor,  # ty: ignore[unresolved-attribute]
                    has_more=result.has_more,  # ty: ignore[unresolved-attribute]
                )
            case "UnauthorizedError":
                raise DagsterPlusUnauthorizedError(f"Error listing issues: {result.message}")  # ty: ignore[unresolved-attribute]
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error listing issues: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def create_issue(
        self, title: str, description: str, status: IssueStatus | None = None
    ) -> DgApiIssue:
        result = self._client.create_issue(title=title, description=description, status=status)

        result = result.create_issue

        match result.typename__:
            case "CreateIssueSuccess":
                return self._build_issue(result.issue)  # ty: ignore[unresolved-attribute]
            case "UnauthorizedError":
                raise DagsterPlusUnauthorizedError(f"Error creating issue: {result.message}")  # ty: ignore[unresolved-attribute]
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error creating issue: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def update_issue(
        self,
        issue_id: str,
        status: IssueStatus | None = None,
        title: str | None = None,
        description: str | None = None,
        context: str | None = None,
    ) -> DgApiIssue:
        result = self._client.update_issue(
            issue_id=issue_id,
            status=status,
            title=title,
            description=description,
            context=context,
        ).update_issue

        match result.typename__:
            case "UpdateIssueSuccess":
                return self._build_issue(result.issue)  # ty: ignore[unresolved-attribute]
            case "UnauthorizedError":
                raise DagsterPlusUnauthorizedError(f"Error updating issue: {result.message}")  # ty: ignore[unresolved-attribute]
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error updating issue: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def create_link_on_issue(
        self,
        issue_id: str,
        run_id: str | None = None,
        asset_key: list[str] | None = None,
    ) -> DgApiIssue:
        linked_object = IssueLinkedObjectInput(
            runId=run_id,
            assetKey=AssetKeyInput(path=asset_key) if asset_key is not None else None,
        )
        result = self._client.add_link_to_issue(
            issue_id=issue_id, linked_object=linked_object
        ).add_link_to_issue

        match result.typename__:
            case "UpdateIssueSuccess":
                return self._build_issue(result.issue)  # ty: ignore[unresolved-attribute]
            case "UnauthorizedError":
                raise DagsterPlusUnauthorizedError(f"Error adding link to issue: {result.message}")  # ty: ignore[unresolved-attribute]
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error adding link to issue: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def delete_link_from_issue(
        self,
        issue_id: str,
        run_id: str | None = None,
        asset_key: list[str] | None = None,
    ) -> DgApiIssue:
        linked_object = IssueLinkedObjectInput(
            runId=run_id,
            assetKey=AssetKeyInput(path=asset_key) if asset_key is not None else None,
        )
        result = self._client.remove_link_from_issue(
            issue_id=issue_id, linked_object=linked_object
        ).remove_link_from_issue

        match result.typename__:
            case "UpdateIssueSuccess":
                return self._build_issue(result.issue)  # ty: ignore[unresolved-attribute]
            case "UnauthorizedError":
                raise DagsterPlusUnauthorizedError(
                    f"Error removing link from issue: {result.message}"  # ty: ignore[unresolved-attribute]
                )
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error removing link from issue: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def _build_issue(self, issue: IssueFields) -> DgApiIssue:
        linked_objects: list[DgApiIssueLinkedRun | DgApiIssueLinkedAsset] = []
        for lo in issue.linked_objects:
            match lo.typename__:
                case "Asset":
                    linked_objects.append(DgApiIssueLinkedAsset(asset_key="/".join(lo.key.path)))  # ty: ignore[unresolved-attribute]
                case "Run":
                    linked_objects.append(DgApiIssueLinkedRun(run_id=lo.id))  # ty: ignore[unresolved-attribute]
                case _ as unreachable:
                    assert_never(unreachable)

        return DgApiIssue(
            id=issue.public_id,
            title=issue.title,
            description=issue.description,
            status=issue.status,
            created_by_name=issue.created_by.display_name if issue.created_by else "",
            linked_objects=linked_objects,
            context=issue.context,
        )
