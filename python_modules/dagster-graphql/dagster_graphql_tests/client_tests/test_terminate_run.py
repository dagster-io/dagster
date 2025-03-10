import pytest
from dagster._core.utils import make_new_run_id
from dagster_graphql import DagsterGraphQLClientError

from dagster_graphql_tests.client_tests.conftest import MockClient, python_client_test_suite

RUN_ID = make_new_run_id()


@python_client_test_suite
def test_terminate_run_status_success(mock_client: MockClient):
    expected_result = None
    response = {"terminateRun": {"__typename": "TerminateRunSuccess", "run": expected_result}}
    mock_client.mock_gql_client.execute.return_value = response

    actual_result = mock_client.python_client.terminate_run(RUN_ID)
    assert actual_result == expected_result


@python_client_test_suite
def test_force_terminate_run_status_success(mock_client: MockClient):
    expected_result = None
    response = {"terminateRun": {"__typename": "TerminateRunSuccess", "run": expected_result}}
    mock_client.mock_gql_client.execute.return_value = response

    actual_result = mock_client.python_client.terminate_run(RUN_ID, True)
    assert actual_result == expected_result


@python_client_test_suite
def test_terminate_run_not_failure(mock_client: MockClient):
    error_type, error_message = "TerminateRunFailure", "Unable to terminate run"
    response = {"terminateRun": {"__typename": "TerminateRunFailure", "message": error_message}}
    mock_client.mock_gql_client.execute.return_value = response

    with pytest.raises(DagsterGraphQLClientError) as e:
        mock_client.python_client.terminate_run(RUN_ID)
    assert e.value.args == (error_type, error_message)


@python_client_test_suite
def test_terminate_run_not_found(mock_client: MockClient):
    error_type, error_message = "RunNotFoundError", f"Run Id {RUN_ID} not found"
    response = {"terminateRun": {"__typename": "RunNotFoundError", "runId": error_message}}

    with pytest.raises(DagsterGraphQLClientError) as e:
        mock_client.mock_gql_client.execute.return_value = response
        mock_client.python_client.terminate_run(RUN_ID)
    assert e.value.args == (error_type, error_message)


@python_client_test_suite
def test_terminate_run_python_error(mock_client: MockClient):
    error_type, error_message = "PythonError", "Unable to terminate run"
    response = {"terminateRun": {"__typename": "PythonError", "message": error_message}}

    with pytest.raises(DagsterGraphQLClientError) as e:
        mock_client.mock_gql_client.execute.return_value = response
        mock_client.python_client.terminate_run(RUN_ID)
    assert e.value.args == (error_type, error_message)
