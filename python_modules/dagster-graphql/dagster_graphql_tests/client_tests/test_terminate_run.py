import time
from urllib import response

import pytest
from dagster_graphql import DagsterGraphQLClientError
from dagster_graphql.client.query import LAUNCH_PIPELINE_EXECUTION_MUTATION
from dagster_graphql.test.utils import execute_dagster_graphql, infer_pipeline_selector

from dagster.core.storage.pipeline_run import PipelineRunStatus

from ..graphql.graphql_context_test_suite import ExecutingGraphQLContextTestMatrix
from ..graphql.setup import csv_hello_world_solids_config
from .conftest import MockClient, python_client_test_suite

RUN_ID = "foo"

@python_client_test_suite
def test_terminate_run_status_success(mock_client: MockClient):
    expected_result = None
    response = {"terminateRun": {"__typename": "TerminateRunSuccess", "run": expected_result}}
    mock_client.mock_gql_client.execute.return_value = response

    actual_result = mock_client.python_client.terminate_run(RUN_ID)
    assert actual_result == expected_result

@python_client_test_suite
def test_terminate_run_not_failure(mock_client: MockClient):
    expected_result = "Unable to terminate run"
    response = {"terminateRun": {"__typename": "TerminateRunFailure", "message": expected_result}}
    mock_client.mock_gql_client.execute.return_value = response

    with pytest.raises(DagsterGraphQLClientError) as e:
        mock_client.python_client.terminate_run(RUN_ID)
        assert e.value.message == expected_result

@python_client_test_suite
def test_terminate_run_not_found(mock_client: MockClient):
    expected_result = "Run Id foo not found"
    response = {"terminateRun": {"__typename": "RunNotFoundError", "runId": expected_result}}

    with pytest.raises(DagsterGraphQLClientError) as e:
        mock_client.mock_gql_client.execute.return_value = response
        mock_client.python_client.terminate_run(RUN_ID)
        assert e.value.message == expected_result

@python_client_test_suite
def test_terminate_run_python_error(mock_client: MockClient):
    expected_result = "Unable to terminate run"
    response = {"terminateRun": {"__typename": "PythonError", "message": expected_result}}

    with pytest.raises(DagsterGraphQLClientError) as e:
        mock_client.mock_gql_client.execute.return_value = response
        mock_client.python_client.terminate_run(RUN_ID)
        assert e.value.message == expected_result
