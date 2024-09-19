import pytest
from dagster._core.utils import make_new_run_id
from dagster_graphql import DagsterGraphQLClientError

from dagster_graphql_tests.client_tests.conftest import MockClient, python_client_test_suite

RUN_IDS = [make_new_run_id(), make_new_run_id(), make_new_run_id()]


@python_client_test_suite
def test_successful_run_termination(mock_client: MockClient):
    expected_result = None
    response = {
        "terminateRuns": {
            "terminateRunResults": [
                {"__typename": "TerminateRunSuccess", "run": {"runId": run_id}}
                for run_id in RUN_IDS
            ]
        }
    }
    mock_client.mock_gql_client.execute.return_value = response

    actual_result = mock_client.python_client.terminate_runs(RUN_IDS)
    assert actual_result == expected_result


@python_client_test_suite
def test_complete_failure_run_not_found(mock_client: MockClient):
    error_messages = [("RunNotFoundError", f"Run Id {run_id} not found") for run_id in RUN_IDS]
    error_message_string = f"All run terminations failed: {error_messages}"
    response = {
        "terminateRuns": {
            "terminateRunResults": [
                {
                    "__typename": "RunNotFoundError",
                    "message": f"Run Id {run_id} not found",
                    "runId": run_id,
                }
                for run_id in RUN_IDS
            ]
        }
    }
    mock_client.mock_gql_client.execute.return_value = response

    with pytest.raises(DagsterGraphQLClientError) as exc_info:
        mock_client.python_client.terminate_runs(RUN_IDS)

    assert str(exc_info.value.args[0]) == "TerminateRunsError"
    assert exc_info.value.args[1] == error_message_string


@python_client_test_suite
def test_partial_failure_due_to_not_found_error(mock_client: MockClient):
    failed_ids = [RUN_IDS[0]]
    success_ids = RUN_IDS[1:]

    error_messages = [("RunNotFoundError", f"Run Id {run_id} not found") for run_id in failed_ids]
    error_message_string = f"Some runs could not be terminated: {error_messages}"

    response = {
        "terminateRuns": {
            "terminateRunResults": [
                {"__typename": "TerminateRunSuccess", "runId": run_id} for run_id in success_ids
            ]
            + [
                {
                    "__typename": "RunNotFoundError",
                    "message": f"Run Id {run_id} not found",
                    "runId": run_id,
                }
                for run_id in failed_ids
            ]
        }
    }
    mock_client.mock_gql_client.execute.return_value = response

    with pytest.raises(DagsterGraphQLClientError) as exc_info:
        mock_client.python_client.terminate_runs(RUN_IDS)

    assert str(exc_info.value.args[0]) == "TerminateRunsError"
    assert exc_info.value.args[1] == error_message_string


@python_client_test_suite
def test_complete_failure_generic_error(mock_client: MockClient):
    error_messages = [("TerminateRunFailure", "Unable to terminate run") for _ in RUN_IDS]
    error_message_string = f"All run terminations failed: {error_messages}"
    response = {
        "terminateRuns": {
            "terminateRunResults": [
                {"__typename": "TerminateRunFailure", "message": "Unable to terminate run"}
                for _ in RUN_IDS
            ]
        }
    }
    mock_client.mock_gql_client.execute.return_value = response

    with pytest.raises(DagsterGraphQLClientError) as exc_info:
        mock_client.python_client.terminate_runs(RUN_IDS)

    assert str(exc_info.value.args[0]) == "TerminateRunsError"
    assert exc_info.value.args[1] == error_message_string


@python_client_test_suite
def test_partial_failure_generic_error(mock_client: MockClient):
    success_ids = [RUN_IDS[0]]
    failed_ids = RUN_IDS[1:]

    error_messages = [("TerminateRunFailure", "Unable to terminate run") for _ in failed_ids]
    error_message_string = f"Some runs could not be terminated: {error_messages}"

    response = {
        "terminateRuns": {
            "terminateRunResults": [
                {"__typename": "TerminateRunSuccess", "run": {"runId": run_id}}
                for run_id in success_ids
            ]
            + [
                {"__typename": "TerminateRunFailure", "message": "Unable to terminate run"}
                for run_id in failed_ids
            ]
        }
    }
    mock_client.mock_gql_client.execute.return_value = response

    with pytest.raises(DagsterGraphQLClientError) as exc_info:
        mock_client.python_client.terminate_runs(RUN_IDS)

    assert str(exc_info.value.args[0]) == "TerminateRunsError"
    assert exc_info.value.args[1] == error_message_string


@python_client_test_suite
def test_complete_failure_python_error(mock_client: MockClient):
    error_messages = [("PythonError", "Unable to terminate run") for _ in RUN_IDS]
    error_message_string = f"All run terminations failed: {error_messages}"
    response = {
        "terminateRuns": {
            "terminateRunResults": [
                {"__typename": "PythonError", "message": "Unable to terminate run"} for _ in RUN_IDS
            ]
        }
    }
    mock_client.mock_gql_client.execute.return_value = response

    with pytest.raises(DagsterGraphQLClientError) as exc_info:
        mock_client.python_client.terminate_runs(RUN_IDS)

    assert str(exc_info.value.args[0]) == "TerminateRunsError"
    assert exc_info.value.args[1] == error_message_string


@python_client_test_suite
def test_partial_failure_python_error(mock_client: MockClient):
    success_ids = [RUN_IDS[0]]
    failed_ids = RUN_IDS[1:]

    error_messages = [("PythonError", "Unable to terminate run") for _ in failed_ids]
    error_message_string = f"Some runs could not be terminated: {error_messages}"

    response = {
        "terminateRuns": {
            "terminateRunResults": [
                {"__typename": "TerminateRunSuccess", "run": {"runId": run_id}}
                for run_id in success_ids
            ]
            + [
                {"__typename": "PythonError", "message": "Unable to terminate run"}
                for _ in failed_ids
            ]
        }
    }
    mock_client.mock_gql_client.execute.return_value = response

    with pytest.raises(DagsterGraphQLClientError) as exc_info:
        mock_client.python_client.terminate_runs(RUN_IDS)

    assert str(exc_info.value.args[0]) == "TerminateRunsError"
    assert exc_info.value.args[1] == error_message_string


@python_client_test_suite
def test_terminate_runs_mixed_results(mock_client: MockClient):
    success_id = RUN_IDS[0]
    not_found_id = RUN_IDS[1]

    error_messages = [
        ("RunNotFoundError", f"Run Id {not_found_id} not found"),
        ("PythonError", "Internal server error occurred"),
    ]
    error_message_string = f"Some runs could not be terminated: {error_messages}"

    response = {
        "terminateRuns": {
            "terminateRunResults": [
                {"__typename": "TerminateRunSuccess", "run": {"runId": success_id}},
                {
                    "__typename": "RunNotFoundError",
                    "message": f"Run Id {not_found_id} not found",
                    "runId": not_found_id,
                },
                {
                    "__typename": "PythonError",
                    "message": "Internal server error occurred",
                    "stack": "Traceback info",
                },
            ]
        }
    }
    mock_client.mock_gql_client.execute.return_value = response

    with pytest.raises(DagsterGraphQLClientError) as exc_info:
        mock_client.python_client.terminate_runs(RUN_IDS)

    assert str(exc_info.value.args[0]) == "TerminateRunsError"
    assert exc_info.value.args[1] == error_message_string
