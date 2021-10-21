import pytest
from dagster import DagsterInvalidDefinitionError
from dagster_graphql import DagsterGraphQLClientError, InvalidOutputErrorInfo

from .conftest import MockClient, python_client_test_suite

EXPECTED_RUN_ID = "foo"

launch_pipeline_success_response = {
    "launchPipelineExecution": {
        "__typename": "LaunchRunSuccess",
        "run": {"runId": EXPECTED_RUN_ID},
    }
}


@python_client_test_suite
def test_success(mock_client: MockClient):
    mock_client.mock_gql_client.execute.return_value = launch_pipeline_success_response
    actual_run_id = mock_client.python_client.submit_pipeline_execution(
        "bar",
        repository_location_name="baz",
        repository_name="quux",
        run_config={},
        mode="default",
    )
    assert actual_run_id == EXPECTED_RUN_ID


@python_client_test_suite
def test_job_success(mock_client: MockClient):
    mock_client.mock_gql_client.execute.return_value = launch_pipeline_success_response
    actual_run_id = mock_client.python_client.submit_job_execution(
        "bar",
        repository_location_name="baz",
        repository_name="quux",
    )
    assert actual_run_id == EXPECTED_RUN_ID


@python_client_test_suite
def test_preset_success(mock_client: MockClient):
    mock_client.mock_gql_client.execute.return_value = launch_pipeline_success_response
    actual_run_id = mock_client.python_client.submit_pipeline_execution(
        "bar", repository_location_name="baz", repository_name="quux", preset="cool_preset"
    )
    assert actual_run_id == EXPECTED_RUN_ID


@python_client_test_suite
def test_tags_success(mock_client: MockClient):
    mock_client.mock_gql_client.execute.return_value = launch_pipeline_success_response
    actual_run_id = mock_client.python_client.submit_pipeline_execution(
        "bar",
        repository_location_name="baz",
        repository_name="quuz",
        run_config={},
        mode="default",
        tags={"my_tag": "a", "my_other_tag": "b"},
    )
    assert actual_run_id == EXPECTED_RUN_ID


@python_client_test_suite
def test_job_tags_success(mock_client: MockClient):
    mock_client.mock_gql_client.execute.return_value = launch_pipeline_success_response
    actual_run_id = mock_client.python_client.submit_job_execution(
        "bar",
        repository_location_name="baz",
        repository_name="quuz",
        tags={"my_tag": "a", "my_other_tag": "b"},
    )
    assert actual_run_id == EXPECTED_RUN_ID


@python_client_test_suite
def test_complex_tags_success(mock_client: MockClient):
    response = {
        "launchPipelineExecution": {
            "__typename": "LaunchRunSuccess",
            "run": {"runId": EXPECTED_RUN_ID},
        }
    }
    mock_client.mock_gql_client.execute.return_value = response
    actual_run_id = mock_client.python_client.submit_pipeline_execution(
        "bar",
        repository_location_name="baz",
        repository_name="quuz",
        run_config={},
        mode="default",
        tags={"my_tag": {"I'm": {"a JSON-encodable": "thing"}}},
    )
    assert actual_run_id == EXPECTED_RUN_ID

    actual_run_id = mock_client.python_client.submit_job_execution(
        "bar",
        repository_location_name="baz",
        repository_name="quuz",
        run_config={},
        tags={"my_tag": {"I'm": {"a JSON-encodable": "thing"}}},
    )
    assert actual_run_id == EXPECTED_RUN_ID


@python_client_test_suite
def test_invalid_tags_failure(mock_client: MockClient):
    class SomeWeirdObject:
        pass

    with pytest.raises(DagsterInvalidDefinitionError):
        mock_client.python_client.submit_pipeline_execution(
            "bar",
            repository_location_name="baz",
            repository_name="quuz",
            run_config={},
            mode="default",
            tags={"my_invalid_tag": SomeWeirdObject()},
        )

    with pytest.raises(DagsterInvalidDefinitionError):
        mock_client.python_client.submit_job_execution(
            "bar",
            repository_location_name="baz",
            repository_name="quuz",
            run_config={},
            tags={"my_invalid_tag": SomeWeirdObject()},
        )


@python_client_test_suite
def test_no_location_or_repo_provided_success(mock_client: MockClient):
    repo_loc_name, repo_name, pipeline_name = "bar", "baz", "quux"
    other_repo_name, other_pipeline_name = "other repo", "my_pipeline"
    get_locations_and_names_response = {
        "repositoriesOrError": {
            "__typename": "RepositoryConnection",
            "nodes": [
                {
                    "name": repo_name,
                    "location": {"name": repo_loc_name},
                    "pipelines": [{"name": pipeline_name}, {"name": other_pipeline_name}],
                },
                {
                    "name": other_repo_name,
                    "location": {"name": repo_loc_name},
                    "pipelines": [{"name": "fun pipeline"}, {"name": other_pipeline_name}],
                },
            ],
        }
    }
    submit_execution_response = {
        "launchPipelineExecution": {
            "__typename": "LaunchRunSuccess",
            "run": {"runId": EXPECTED_RUN_ID},
        }
    }
    mock_client.mock_gql_client.execute.side_effect = [
        get_locations_and_names_response,
        submit_execution_response,
    ]

    actual_run_id = mock_client.python_client.submit_pipeline_execution(
        pipeline_name, run_config={}, mode="default"
    )
    assert actual_run_id == EXPECTED_RUN_ID

    mock_client.mock_gql_client.execute.side_effect = [
        get_locations_and_names_response,
        submit_execution_response,
    ]

    actual_run_id = mock_client.python_client.submit_job_execution(pipeline_name, run_config={})
    assert actual_run_id == EXPECTED_RUN_ID


def no_location_or_repo_provided_duplicate_pipeline_mock_config(mock_client: MockClient):
    repo_loc_name, repo_name, pipeline_name = "bar", "baz", "quux"
    other_repo_name = "other repo"
    get_locations_and_names_response = {
        "repositoriesOrError": {
            "__typename": "RepositoryConnection",
            "nodes": [
                {
                    "name": repo_name,
                    "location": {"name": repo_loc_name},
                    "pipelines": [{"name": pipeline_name}],
                },
                {
                    "name": other_repo_name,
                    "location": {"name": repo_loc_name},
                    "pipelines": [{"name": pipeline_name}],
                },
            ],
        }
    }
    submit_execution_response = {
        "launchPipelineExecution": {
            "__typename": "LaunchRunSuccess",
            "run": {"runId": EXPECTED_RUN_ID},
        }
    }
    mock_client.mock_gql_client.execute.side_effect = [
        get_locations_and_names_response,
        submit_execution_response,
    ]

    return pipeline_name


@python_client_test_suite
def test_no_location_or_repo_provided_duplicate_pipeline_failure(mock_client: MockClient):
    pipeline_name = no_location_or_repo_provided_duplicate_pipeline_mock_config(mock_client)

    with pytest.raises(DagsterGraphQLClientError) as exc_info:
        mock_client.python_client.submit_pipeline_execution(
            pipeline_name, run_config={}, mode="default"
        )

    assert exc_info.value.args[0].find(f"multiple pipelines with the name {pipeline_name}") != -1


@python_client_test_suite
def test_no_location_or_repo_provided_duplicate_job_failure(mock_client: MockClient):
    job_name = no_location_or_repo_provided_duplicate_pipeline_mock_config(mock_client)

    with pytest.raises(DagsterGraphQLClientError) as exc_info:
        mock_client.python_client.submit_job_execution(job_name, run_config={})

    assert exc_info.value.args[0].find(f"multiple jobs with the name {job_name}") != -1


def no_location_or_repo_provided_mock_config(mock_client):
    repo_loc_name, repo_name, pipeline_name = "bar", "baz", "quux"
    get_locations_and_names_response = {
        "repositoriesOrError": {
            "__typename": "RepositoryConnection",
            "nodes": [
                {
                    "name": repo_name,
                    "location": {"name": repo_loc_name},
                    "pipelines": [{"name": pipeline_name}],
                }
            ],
        }
    }
    submit_execution_response = {
        "launchPipelineExecution": {
            "__typename": "LaunchRunSuccess",
            "run": {"runId": EXPECTED_RUN_ID},
        }
    }
    mock_client.mock_gql_client.execute.side_effect = [
        get_locations_and_names_response,
        submit_execution_response,
    ]


@python_client_test_suite
def test_no_location_or_repo_provided_no_pipeline_failure(mock_client: MockClient):
    no_location_or_repo_provided_mock_config(mock_client)

    with pytest.raises(DagsterGraphQLClientError) as exc_info:
        mock_client.python_client.submit_pipeline_execution("123", run_config={}, mode="default")

    assert exc_info.value.args[0] == "PipelineNotFoundError"


@python_client_test_suite
def test_no_location_or_repo_provided_no_job_failure(mock_client: MockClient):
    no_location_or_repo_provided_mock_config(mock_client)

    with pytest.raises(DagsterGraphQLClientError) as exc_info:
        mock_client.python_client.submit_job_execution("123", run_config={})

    assert exc_info.value.args[0] == "JobNotFoundError"


@python_client_test_suite
def test_failure_with_invalid_step_error(mock_client: MockClient):
    error_type, invalid_step_key = "InvalidStepError", "1234"
    response = {
        "launchPipelineExecution": {
            "__typename": error_type,
            "invalidStepKey": invalid_step_key,
        }
    }
    mock_client.mock_gql_client.execute.return_value = response

    with pytest.raises(DagsterGraphQLClientError) as exc_info:
        mock_client.python_client.submit_pipeline_execution(
            "bar",
            repository_location_name="baz",
            repository_name="quux",
            run_config={},
            mode="default",
        )
    exc_args = exc_info.value.args

    assert exc_args[0] == error_type
    assert exc_args[1] == invalid_step_key


@python_client_test_suite
def test_failure_with_invalid_output_error(mock_client: MockClient):
    error_type, step_key, invalid_output_name = "InvalidOutputError", "1234", "some output"
    response = {
        "launchPipelineExecution": {
            "__typename": error_type,
            "stepKey": step_key,
            "invalidOutputName": invalid_output_name,
        }
    }
    mock_client.mock_gql_client.execute.return_value = response

    with pytest.raises(DagsterGraphQLClientError) as exc_info:
        mock_client.python_client.submit_pipeline_execution(
            "bar",
            repository_location_name="baz",
            repository_name="quux",
            run_config={},
            mode="default",
        )

    assert exc_info.value.args == (error_type,)
    assert exc_info.value.body == InvalidOutputErrorInfo(
        step_key=step_key, invalid_output_name=invalid_output_name
    )


@python_client_test_suite
def test_failure_with_pipeline_config_invalid(mock_client: MockClient):
    error_type = "RunConfigValidationInvalid"
    errors = [
        {
            "__typename": "some_error",
            "message": "AWS warehouse got hit by a meteor",
            "path": [],
            "reason": "Network failure",
        }
    ]
    response = {"launchPipelineExecution": {"__typename": error_type, "errors": errors}}
    mock_client.mock_gql_client.execute.return_value = response

    with pytest.raises(DagsterGraphQLClientError) as exc_info:
        mock_client.python_client.submit_pipeline_execution(
            "bar",
            repository_location_name="baz",
            repository_name="quux",
            run_config={},
            mode="default",
        )
    exc_args = exc_info.value.args

    assert exc_args[0] == error_type
    assert exc_args[1] == errors


@python_client_test_suite
def test_failure_with_python_error(mock_client: MockClient):
    error_type, message = "PythonError", "some catastrophic error"
    response = {
        "launchPipelineExecution": {
            "__typename": error_type,
            "message": message,
        }
    }
    mock_client.mock_gql_client.execute.return_value = response

    with pytest.raises(DagsterGraphQLClientError) as exc_info:
        mock_client.python_client.submit_pipeline_execution(
            "bar",
            repository_location_name="baz",
            repository_name="quux",
            run_config={},
            mode="default",
        )
    exc_args = exc_info.value.args

    assert exc_args[0] == error_type
    assert exc_args[1] == message

    with pytest.raises(DagsterGraphQLClientError) as exc_info:
        mock_client.python_client.submit_job_execution(
            "bar",
            repository_location_name="baz",
            repository_name="quux",
            run_config={},
        )
    exc_args = exc_info.value.args

    assert exc_args[0] == error_type
    assert exc_args[1] == message


def failure_with_pipeline_run_conflict_mock_config(mock_client: MockClient):
    error_type, message = "RunConflict", "some conflict"
    response = {
        "launchPipelineExecution": {
            "__typename": error_type,
            "message": message,
        }
    }
    mock_client.mock_gql_client.execute.return_value = response


@python_client_test_suite
def test_failure_with_pipeline_run_conflict(mock_client: MockClient):
    failure_with_pipeline_run_conflict_mock_config(mock_client)

    with pytest.raises(DagsterGraphQLClientError) as exc_info:
        mock_client.python_client.submit_pipeline_execution(
            "bar",
            repository_location_name="baz",
            repository_name="quux",
            run_config={},
            mode="default",
        )
    exc_args = exc_info.value.args

    assert exc_args[0] == "RunConflict"
    assert exc_args[1] == "some conflict"


@python_client_test_suite
def test_failure_with_job_run_conflict(mock_client: MockClient):
    failure_with_pipeline_run_conflict_mock_config(mock_client)

    with pytest.raises(DagsterGraphQLClientError) as exc_info:
        mock_client.python_client.submit_job_execution(
            "bar",
            repository_location_name="baz",
            repository_name="quux",
            run_config={},
        )
    exc_args = exc_info.value.args

    assert exc_args[0] == "RunConflict"
    assert exc_args[1] == "some conflict"


@python_client_test_suite
def test_failure_with_query_error(mock_client: MockClient):
    mock_client.mock_gql_client.side_effect = Exception("foo")

    with pytest.raises(DagsterGraphQLClientError) as exc_info:
        mock_client.python_client.submit_pipeline_execution(
            "bar",
            repository_location_name="baz",
            repository_name="quux",
            run_config={},
            mode="default",
        )

    assert exc_info.value.args[0].endswith("failed GraphQL validation")
