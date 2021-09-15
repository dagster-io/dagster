import pytest
from dagster_graphql import DagsterGraphQLClientError

from .conftest import MockClient, python_client_test_suite

EXPECTED_RUN_ID = "foo"


@python_client_test_suite
def test_success(mock_client: MockClient):
    response = {
        "terminatePipelineExecution": {
            "__typename": "TerminatePipelineExecutionSuccess",
            "run": {"runId": EXPECTED_RUN_ID},
        }
    }
    mock_client.mock_gql_client.execute.return_value = response
    actual_run_id = mock_client.python_client.terminate_pipeline(
        run_id="bar",
    )
    assert actual_run_id == EXPECTED_RUN_ID


@python_client_test_suite
def test_pipeline_not_found(mock_client: MockClient):
    response = {
        "terminatePipelineExecution": {
            "__typename": "PipelineRunNotFoundError",
            "runId": EXPECTED_RUN_ID,
        }
    }
    mock_client.mock_gql_client.execute.return_value = response

    with pytest.raises(DagsterGraphQLClientError) as exc_info:
        mock_client.python_client.terminate_pipeline(
            run_id="bar",
        )

    assert exc_info.value.args[0] == "PipelineRunNotFoundError"


@python_client_test_suite
def test_failure(mock_client: MockClient):
    error_type, message = "TerminatePipelineExecutionFailure", "something went wrong"
    response = {
        "terminatePipelineExecution": {
            "__typename": error_type,
            "message": message,
        }
    }
    mock_client.mock_gql_client.execute.return_value = response

    with pytest.raises(DagsterGraphQLClientError) as exc_info:
        mock_client.python_client.terminate_pipeline(
            run_id="bar",
        )

    assert exc_info.value.args == (error_type, message)
