from unittest.mock import Mock

import pytest
from dagster_rest_resources.__generated__.add_link_to_issue import (
    AddLinkToIssue,
    AddLinkToIssueAddLinkToIssuePythonError,
    AddLinkToIssueAddLinkToIssueUnauthorizedError,
    AddLinkToIssueAddLinkToIssueUpdateIssueSuccess,
    AddLinkToIssueAddLinkToIssueUpdateIssueSuccessIssue,
)
from dagster_rest_resources.__generated__.create_issue import (
    CreateIssue,
    CreateIssueCreateIssueCreateIssueSuccess,
    CreateIssueCreateIssueCreateIssueSuccessIssue,
    CreateIssueCreateIssuePythonError,
    CreateIssueCreateIssueUnauthorizedError,
)
from dagster_rest_resources.__generated__.enums import IssueStatus
from dagster_rest_resources.__generated__.fragments import (
    IssueFieldsCreatedByDagsterCloudUser,
    IssueFieldsLinkedObjectsAsset,
    IssueFieldsLinkedObjectsAssetKey,
    IssueFieldsLinkedObjectsRun,
)
from dagster_rest_resources.__generated__.get_issue import (
    GetIssue,
    GetIssueIssueIssue,
    GetIssueIssuePythonError,
    GetIssueIssueUnauthorizedError,
)
from dagster_rest_resources.__generated__.list_issues import (
    ListIssues,
    ListIssuesIssuesIssueConnection,
    ListIssuesIssuesIssueConnectionIssues,
    ListIssuesIssuesPythonError,
    ListIssuesIssuesUnauthorizedError,
)
from dagster_rest_resources.__generated__.remove_link_from_issue import (
    RemoveLinkFromIssue,
    RemoveLinkFromIssueRemoveLinkFromIssuePythonError,
    RemoveLinkFromIssueRemoveLinkFromIssueUnauthorizedError,
    RemoveLinkFromIssueRemoveLinkFromIssueUpdateIssueSuccess,
    RemoveLinkFromIssueRemoveLinkFromIssueUpdateIssueSuccessIssue,
)
from dagster_rest_resources.__generated__.update_issue import (
    UpdateIssue,
    UpdateIssueUpdateIssuePythonError,
    UpdateIssueUpdateIssueUnauthorizedError,
    UpdateIssueUpdateIssueUpdateIssueSuccess,
    UpdateIssueUpdateIssueUpdateIssueSuccessIssue,
)
from dagster_rest_resources.api.issue import DgApiIssueApi
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.exception import (
    DagsterPlusGraphqlError,
    DagsterPlusUnauthorizedError,
)
from dagster_rest_resources.schemas.issue import (
    DgApiIssueLinkedAsset,
    DgApiIssueLinkedRun,
    DgApiIssueList,
)


def _make_issue_fields(**kwargs) -> dict:
    defaults = dict(
        publicId="issue-1",
        title="test issue",
        description="test description",
        status=IssueStatus.OPEN,
        context=None,
        linkedObjects=[],
        createdBy=IssueFieldsCreatedByDagsterCloudUser(
            __typename="DagsterCloudUser", displayName="test@email.com"
        ),
    )
    defaults.update(kwargs)
    return defaults


class TestGetIssue:
    def test_returns_issue(self):
        client = Mock(spec=IGraphQLClient)
        client.get_issue.return_value = GetIssue(
            issue=GetIssueIssueIssue(
                __typename="Issue",
                **_make_issue_fields(
                    linkedObjects=[
                        IssueFieldsLinkedObjectsRun(
                            __typename="Run",
                            id="run-123",
                        ),
                        IssueFieldsLinkedObjectsAsset(
                            __typename="Asset",
                            key=IssueFieldsLinkedObjectsAssetKey(path=["test", "asset"]),
                        ),
                    ]
                ),
            )
        )

        result = DgApiIssueApi(_client=client).get_issue("issue-abc")

        assert result.id == "issue-1"
        assert result.title == "test issue"
        assert result.description == "test description"
        assert result.status == IssueStatus.OPEN
        assert result.context is None
        assert len(result.linked_objects) == 2
        assert isinstance(result.linked_objects[0], DgApiIssueLinkedRun)
        assert result.linked_objects[0].run_id == "run-123"
        assert isinstance(result.linked_objects[1], DgApiIssueLinkedAsset)
        assert result.linked_objects[1].asset_key == "test/asset"
        assert result.created_by_name == "test@email.com"

    def test_none_response_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_issue.return_value = GetIssue(issue=None)

        with pytest.raises(DagsterPlusGraphqlError, match="Issue not found"):
            DgApiIssueApi(_client=client).get_issue("missing")

    def test_unauthorized_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_issue.return_value = GetIssue(
            issue=GetIssueIssueUnauthorizedError(__typename="UnauthorizedError", message="")
        )

        with pytest.raises(DagsterPlusUnauthorizedError, match="Error fetching issue"):
            DgApiIssueApi(_client=client).get_issue("")

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_issue.return_value = GetIssue(
            issue=GetIssueIssuePythonError(__typename="PythonError", message="")
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error fetching issue"):
            DgApiIssueApi(_client=client).get_issue("")


class TestListIssues:
    def test_returns_issues(self):
        client = Mock(spec=IGraphQLClient)
        client.list_issues.return_value = ListIssues(
            issues=ListIssuesIssuesIssueConnection(
                __typename="IssueConnection",
                issues=[
                    ListIssuesIssuesIssueConnectionIssues(**_make_issue_fields(publicId="issue-1")),
                    ListIssuesIssuesIssueConnectionIssues(**_make_issue_fields(publicId="issue-2")),
                ],
                cursor=None,
                hasMore=False,
            )
        )

        result = DgApiIssueApi(_client=client).list_issues()

        assert len(result.items) == 2
        assert result.items[0].id == "issue-1"
        assert result.items[1].id == "issue-2"
        assert result.cursor is None
        assert result.has_more is False

    def test_returns_empty_list(self):
        client = Mock(spec=IGraphQLClient)
        client.list_issues.return_value = ListIssues(
            issues=ListIssuesIssuesIssueConnection(
                __typename="IssueConnection",
                issues=[],
                cursor=None,
                hasMore=False,
            )
        )

        result = DgApiIssueApi(_client=client).list_issues()

        assert result == DgApiIssueList(items=[], cursor=None, has_more=False)

    def test_returns_paginated_list(self):
        client = Mock(spec=IGraphQLClient)
        client.list_issues.return_value = ListIssues(
            issues=ListIssuesIssuesIssueConnection(
                __typename="IssueConnection",
                issues=[ListIssuesIssuesIssueConnectionIssues(**_make_issue_fields())],
                cursor="next-cursor",
                hasMore=True,
            )
        )

        result = DgApiIssueApi(_client=client).list_issues()

        assert len(result.items) == 1
        assert result.cursor == "next-cursor"
        assert result.has_more is True

    def test_none_response_returns_empty(self):
        client = Mock(spec=IGraphQLClient)
        client.list_issues.return_value = ListIssues(issues=None)

        result = DgApiIssueApi(_client=client).list_issues()

        assert result == DgApiIssueList(items=[], cursor=None, has_more=False)

    def test_passes_filters_to_client(self):
        client = Mock(spec=IGraphQLClient)
        client.list_issues.return_value = ListIssues(
            issues=ListIssuesIssuesIssueConnection(
                __typename="IssueConnection", issues=[], cursor=None, hasMore=False
            )
        )
        DgApiIssueApi(_client=client).list_issues(
            statuses=[IssueStatus.OPEN],
            created_after=1.0,
        )

        call_kwargs = client.list_issues.call_args[1]
        assert call_kwargs["filters"].statuses == [IssueStatus.OPEN]
        assert call_kwargs["filters"].created_after == 1.0

    def test_unauthorized_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_issues.return_value = ListIssues(
            issues=ListIssuesIssuesUnauthorizedError(__typename="UnauthorizedError", message="")
        )

        with pytest.raises(DagsterPlusUnauthorizedError, match="Error listing issues"):
            DgApiIssueApi(_client=client).list_issues()

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_issues.return_value = ListIssues(
            issues=ListIssuesIssuesPythonError(__typename="PythonError", message="")
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error listing issues"):
            DgApiIssueApi(_client=client).list_issues()


class TestCreateIssue:
    def test_creates_issue(self):
        client = Mock(spec=IGraphQLClient)
        client.create_issue.return_value = CreateIssue(
            createIssue=CreateIssueCreateIssueCreateIssueSuccess(
                __typename="CreateIssueSuccess",
                issue=CreateIssueCreateIssueCreateIssueSuccessIssue(
                    **_make_issue_fields(publicId="new-issue", title="", description="")
                ),
            )
        )
        result = DgApiIssueApi(_client=client).create_issue(title="", description="")

        assert result.id == "new-issue"

    def test_unauthorized_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.create_issue.return_value = CreateIssue(
            createIssue=CreateIssueCreateIssueUnauthorizedError(
                __typename="UnauthorizedError", message=""
            )
        )

        with pytest.raises(DagsterPlusUnauthorizedError, match="Error creating issue"):
            DgApiIssueApi(_client=client).create_issue(title="", description="")

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.create_issue.return_value = CreateIssue(
            createIssue=CreateIssueCreateIssuePythonError(__typename="PythonError", message="")
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error creating issue"):
            DgApiIssueApi(_client=client).create_issue(title="", description="")


class TestUpdateIssue:
    def test_updates_issue(self):
        client = Mock(spec=IGraphQLClient)
        client.update_issue.return_value = UpdateIssue(
            updateIssue=UpdateIssueUpdateIssueUpdateIssueSuccess(
                __typename="UpdateIssueSuccess",
                issue=UpdateIssueUpdateIssueUpdateIssueSuccessIssue(
                    **_make_issue_fields(publicId="updated-issue", status=IssueStatus.CLOSED)
                ),
            )
        )
        result = DgApiIssueApi(_client=client).update_issue(
            issue_id="updated-issue", status=IssueStatus.CLOSED
        )

        assert result.id == "updated-issue"

    def test_unauthorized_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.update_issue.return_value = UpdateIssue(
            updateIssue=UpdateIssueUpdateIssueUnauthorizedError(
                __typename="UnauthorizedError", message=""
            )
        )

        with pytest.raises(DagsterPlusUnauthorizedError, match="Error updating issue"):
            DgApiIssueApi(_client=client).update_issue(issue_id="")

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.update_issue.return_value = UpdateIssue(
            updateIssue=UpdateIssueUpdateIssuePythonError(__typename="PythonError", message="")
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error updating issue"):
            DgApiIssueApi(_client=client).update_issue(issue_id="")


class TestCreateLinkOnIssue:
    def test_adds_links(self):
        client = Mock(spec=IGraphQLClient)
        client.add_link_to_issue.return_value = AddLinkToIssue(
            addLinkToIssue=AddLinkToIssueAddLinkToIssueUpdateIssueSuccess(
                __typename="UpdateIssueSuccess",
                issue=AddLinkToIssueAddLinkToIssueUpdateIssueSuccessIssue(
                    **_make_issue_fields(
                        issue_id="test-issue",
                        linkedObjects=[
                            IssueFieldsLinkedObjectsRun(
                                __typename="Run",
                                id="test-run",
                            ),
                            IssueFieldsLinkedObjectsAsset(
                                __typename="Asset",
                                key=IssueFieldsLinkedObjectsAssetKey(path=["test", "asset"]),
                            ),
                        ],
                    )
                ),
            )
        )

        result = DgApiIssueApi(_client=client).create_link_on_issue(
            issue_id="test-issue", run_id="test-run", asset_key=["test", "asset"]
        )

        assert len(result.linked_objects) == 2
        assert isinstance(result.linked_objects[0], DgApiIssueLinkedRun)
        assert result.linked_objects[0].run_id == "test-run"
        assert isinstance(result.linked_objects[1], DgApiIssueLinkedAsset)
        assert result.linked_objects[1].asset_key == "test/asset"

    def test_unauthorized_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.add_link_to_issue.return_value = AddLinkToIssue(
            addLinkToIssue=AddLinkToIssueAddLinkToIssueUnauthorizedError(
                __typename="UnauthorizedError", message=""
            )
        )

        with pytest.raises(DagsterPlusUnauthorizedError, match="Error adding link"):
            DgApiIssueApi(_client=client).create_link_on_issue(issue_id="")

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.add_link_to_issue.return_value = AddLinkToIssue(
            addLinkToIssue=AddLinkToIssueAddLinkToIssuePythonError(
                __typename="PythonError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error adding link"):
            DgApiIssueApi(_client=client).create_link_on_issue(issue_id="")


class TestDeleteLinkFromIssue:
    def test_removes_link(self):
        client = Mock(spec=IGraphQLClient)
        client.remove_link_from_issue.return_value = RemoveLinkFromIssue(
            removeLinkFromIssue=RemoveLinkFromIssueRemoveLinkFromIssueUpdateIssueSuccess(
                __typename="UpdateIssueSuccess",
                issue=RemoveLinkFromIssueRemoveLinkFromIssueUpdateIssueSuccessIssue(
                    **_make_issue_fields(
                        issue_id="test-issue",
                        linkedObjects=[],
                    )
                ),
            )
        )

        result = DgApiIssueApi(_client=client).delete_link_from_issue(
            issue_id="test-issue", run_id="run-xyz", asset_key=["test", "asset"]
        )

        assert result.linked_objects == []

    def test_unauthorized_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.remove_link_from_issue.return_value = RemoveLinkFromIssue(
            removeLinkFromIssue=RemoveLinkFromIssueRemoveLinkFromIssueUnauthorizedError(
                __typename="UnauthorizedError", message=""
            )
        )

        with pytest.raises(DagsterPlusUnauthorizedError, match="Error removing link"):
            DgApiIssueApi(_client=client).delete_link_from_issue(issue_id="")

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.remove_link_from_issue.return_value = RemoveLinkFromIssue(
            removeLinkFromIssue=RemoveLinkFromIssueRemoveLinkFromIssuePythonError(
                __typename="PythonError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error removing link"):
            DgApiIssueApi(_client=client).delete_link_from_issue(issue_id="")
