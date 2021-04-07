import pytest
from dagster_graphql import DagsterGraphQLClientError, ReloadRepositoryLocationStatus

from .conftest import MockClient, python_client_test_suite


@python_client_test_suite
def test_reload_repo_location_success(mock_client: MockClient):
    response = {"reloadRepositoryLocation": {"__typename": "RepositoryLocation"}}
    mock_client.mock_gql_client.execute.return_value = response

    assert (
        mock_client.python_client.reload_repository_location("foo").status
        == ReloadRepositoryLocationStatus.SUCCESS
    )


@python_client_test_suite
def test_reload_repo_location_failure(mock_client: MockClient):
    error_msg = "some reason"
    response = {
        "reloadRepositoryLocation": {
            "__typename": "RepositoryLocationLoadFailure",
            "error": {"message": error_msg},
        }
    }
    mock_client.mock_gql_client.execute.return_value = response

    result = mock_client.python_client.reload_repository_location("foo")
    assert result.status == ReloadRepositoryLocationStatus.FAILURE
    assert result.message == error_msg


@python_client_test_suite
def test_reload_repo_location_fails_with_query_error(mock_client: MockClient):
    mock_client.mock_gql_client.execute.side_effect = Exception("foo")

    with pytest.raises(DagsterGraphQLClientError) as _:
        mock_client.python_client.reload_repository_location("foo")
