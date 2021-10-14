import pytest
from dagster_graphql import DagsterGraphQLClientError, ReloadRepositoryLocationStatus

from ..graphql.graphql_context_test_suite import (
    GraphQLContextVariant,
    make_graphql_context_test_suite,
)
from .conftest import MockClient, python_client_test_suite


@python_client_test_suite
def test_success(mock_client: MockClient):
    response = {
        "reloadRepositoryLocation": {
            "__typename": "WorkspaceLocationEntry",
            "locationOrLoadError": {"__typename": "RepositoryLocation"},
        }
    }
    mock_client.mock_gql_client.execute.return_value = response

    assert (
        mock_client.python_client.reload_repository_location("foo").status
        == ReloadRepositoryLocationStatus.SUCCESS
    )


@python_client_test_suite
def test_failure_with_repo_location_load_failure(mock_client: MockClient):
    error_type, error_msg = "PythonError", "some reason"
    response = {
        "reloadRepositoryLocation": {
            "__typename": "WorkspaceLocationEntry",
            "locationOrLoadError": {
                "__typename": error_type,
                "message": error_msg,
            },
        }
    }
    mock_client.mock_gql_client.execute.return_value = response

    result = mock_client.python_client.reload_repository_location("foo")
    assert result.status == ReloadRepositoryLocationStatus.FAILURE
    assert result.failure_type == error_type
    assert result.message == error_msg


@python_client_test_suite
def test_failure_with_reload_not_supported(mock_client: MockClient):
    error_type, error_msg = "ReloadNotSupported", "some reason"
    response = {
        "reloadRepositoryLocation": {
            "__typename": error_type,
            "message": error_msg,
        }
    }
    mock_client.mock_gql_client.execute.return_value = response

    result = mock_client.python_client.reload_repository_location("foo")
    assert result.status == ReloadRepositoryLocationStatus.FAILURE
    assert result.failure_type == error_type
    assert result.message == error_msg


@python_client_test_suite
def test_failure_with_repo_location_not_found(mock_client: MockClient):
    error_type, error_msg = "RepositoryLocationNotFound", "some reason"
    response = {
        "reloadRepositoryLocation": {
            "__typename": error_type,
            "message": error_msg,
        }
    }
    mock_client.mock_gql_client.execute.return_value = response

    result = mock_client.python_client.reload_repository_location("foo")
    assert result.status == ReloadRepositoryLocationStatus.FAILURE
    assert result.failure_type == error_type
    assert result.message == error_msg


@python_client_test_suite
def test_failure_with_query_error(mock_client: MockClient):
    mock_client.mock_gql_client.execute.side_effect = Exception("foo")

    with pytest.raises(DagsterGraphQLClientError) as _:
        mock_client.python_client.reload_repository_location("foo")


class TestReloadRepositoryLocationWithClient(
    make_graphql_context_test_suite(
        context_variants=[
            GraphQLContextVariant.non_launchable_in_memory_instance_managed_grpc_env()
        ]
    )
):
    def test_reload_location_real(self, graphql_client):
        assert (
            graphql_client.reload_repository_location("test").status
            == ReloadRepositoryLocationStatus.SUCCESS
        )
