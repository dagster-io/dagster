import pytest
from dagster_graphql import DagsterGraphQLClientError
from dagster_graphql.client.query import LAUNCH_PIPELINE_EXECUTION_MUTATION
from dagster_graphql.test.utils import execute_dagster_graphql, infer_pipeline_selector

from ..graphql.graphql_context_test_suite import ExecutingGraphQLContextTestMatrix
from ..graphql.repo import csv_hello_world_ops_config
from .conftest import MockClient, python_client_test_suite


@python_client_test_suite
def test_get_run_tags_success(mock_client: MockClient):
    expected_result = {"tag1": "value1", "tag2": "value2"}
    tags = [{"key": key, "value": value} for key, value in expected_result.items()]
    response = {"pipelineRunOrError": {"__typename": "PipelineRun", "tags": tags}}
    mock_client.mock_gql_client.execute.return_value = response

    actual_result = mock_client.python_client.get_run_tags("foo")
    assert actual_result == expected_result


@python_client_test_suite
def test_get_run_tags_fails_with_python_error(mock_client: MockClient):
    error_type, error_msg = "PythonError", "something exploded"
    response = {"pipelineRunOrError": {"__typename": error_type, "message": error_msg}}
    mock_client.mock_gql_client.execute.return_value = response

    with pytest.raises(DagsterGraphQLClientError) as exc_info:
        mock_client.python_client.get_run_tags("foo")

    assert exc_info.value.args == (error_type, error_msg)


@python_client_test_suite
def test_get_run_tags_fails_with_pipeline_run_not_found_error(mock_client: MockClient):
    error_type, error_msg = "RunNotFoundError", "The specified pipeline run does not exist"
    response = {"pipelineRunOrError": {"__typename": error_type, "message": error_msg}}
    mock_client.mock_gql_client.execute.return_value = response

    with pytest.raises(DagsterGraphQLClientError) as exc_info:
        mock_client.python_client.get_run_tags("foo")

    assert exc_info.value.args == (error_type, error_msg)


@python_client_test_suite
def test_get_run_tags_fails_with_query_error(mock_client: MockClient):
    mock_client.mock_gql_client.execute.side_effect = Exception("foo")

    with pytest.raises(DagsterGraphQLClientError) as _:
        mock_client.python_client.get_run_tags("foo")
    

class TestGetRunTagsWithClient(ExecutingGraphQLContextTestMatrix):
    def test_get_run_tags(self, graphql_context, graphql_client):
        expected_result = {"tag1": "value1", "tag2": "value2"}
        tags = [{"key": key, "value": value} for key, value in expected_result.items()]
        
        selector = infer_pipeline_selector(graphql_context, "csv_hello_world")
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": csv_hello_world_ops_config(),
                    "mode": "default",
                    "executionMetadata": {"tags": tags},
                }
            },
        )

        assert not result.errors
        assert result.data

        run_id = result.data["launchPipelineExecution"]["run"]["runId"]

        actual_result = graphql_client.get_run_tags(run_id)
        
        assert actual_result == expected_result
