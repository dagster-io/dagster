import pytest
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster_graphql import DagsterGraphQLClientError

from .conftest import MockClient, python_client_test_suite


@python_client_test_suite
def test_get_run_status_success(mock_client: MockClient):
    expected_result = PipelineRunStatus.SUCCESS
    response = {"pipelineRunOrError": {"__typename": "PipelineRun", "status": expected_result}}
    mock_client.mock_gql_client.execute.return_value = response

    actual_result = mock_client.python_client.get_run_status("foo")
    assert actual_result == expected_result


@python_client_test_suite
def test_get_run_status_fails_with_python_error(mock_client: MockClient):
    error_type, error_msg = "PythonError", "something exploded"
    response = {"pipelineRunOrError": {"__typename": error_type, "message": error_msg}}
    mock_client.mock_gql_client.execute.return_value = response

    with pytest.raises(DagsterGraphQLClientError) as exc_info:
        mock_client.python_client.get_run_status("foo")

    assert exc_info.value.args == (error_type, error_msg)


@python_client_test_suite
def test_get_run_status_fails_with_pipeline_run_not_found_error(mock_client: MockClient):
    error_type, error_msg = "PipelineRunNotFoundError", "The specified pipeline run does not exist"
    response = {"pipelineRunOrError": {"__typename": error_type, "message": error_msg}}
    mock_client.mock_gql_client.execute.return_value = response

    with pytest.raises(DagsterGraphQLClientError) as exc_info:
        mock_client.python_client.get_run_status("foo")

    assert exc_info.value.args == (error_type, error_msg)


@python_client_test_suite
def test_get_run_status_fails_with_query_error(mock_client: MockClient):
    mock_client.mock_gql_client.execute.side_effect = Exception("foo")

    with pytest.raises(DagsterGraphQLClientError) as _:
        mock_client.python_client.get_run_status("foo")
