from typing import Optional

import pytest
import responses
from dagster import Failure
from dagster_dbt.cloud_v2.resources import DbtCloudCredentials, DbtCloudWorkspace
from dagster_dbt.cloud_v2.types import DbtCloudJobRunStatusType

from dagster_dbt_tests.cloud_v2.conftest import (
    SAMPLE_CUSTOM_CREATE_JOB_RESPONSE,
    TEST_ACCOUNT_ID,
    TEST_CUSTOM_ADHOC_JOB_NAME,
    TEST_DEFAULT_ADHOC_JOB_NAME,
    TEST_ENVIRONMENT_ID,
    TEST_FINISHED_AT_LOWER_BOUND,
    TEST_FINISHED_AT_UPPER_BOUND,
    TEST_JOB_ID,
    TEST_PROJECT_ID,
    TEST_REST_API_BASE_URL,
    TEST_RUN_ID,
    TEST_TOKEN,
    get_sample_run_response,
)


def assert_rest_api_call(
    call: responses.Call,
    endpoint: Optional[str],
    method: Optional[str] = None,
):
    rest_api_url = call.request.url.split("?")[0]
    test_url = f"{TEST_REST_API_BASE_URL}/{endpoint}" if endpoint else TEST_REST_API_BASE_URL
    assert rest_api_url == test_url
    if method:
        assert method == call.request.method
    assert call.request.headers["Authorization"] == f"Token {TEST_TOKEN}"


def test_basic_resource_request(
    workspace: DbtCloudWorkspace,
    all_api_mocks: responses.RequestsMock,
) -> None:
    client = workspace.get_client()

    # jobs data calls
    client.list_jobs(project_id=TEST_PROJECT_ID, environment_id=TEST_ENVIRONMENT_ID)
    client.create_job(
        project_id=TEST_PROJECT_ID,
        environment_id=TEST_ENVIRONMENT_ID,
        job_name=TEST_DEFAULT_ADHOC_JOB_NAME,
    )
    client.trigger_job_run(job_id=TEST_JOB_ID)
    client.get_run_details(run_id=TEST_RUN_ID)
    client.get_run_manifest_json(run_id=TEST_RUN_ID)
    client.get_run_results_json(run_id=TEST_RUN_ID)
    client.get_project_details(project_id=TEST_PROJECT_ID)
    client.get_environment_details(environment_id=TEST_ENVIRONMENT_ID)
    client.get_runs_batch(
        project_id=TEST_PROJECT_ID,
        environment_id=TEST_ENVIRONMENT_ID,
        finished_at_lower_bound=TEST_FINISHED_AT_LOWER_BOUND,
        finished_at_upper_bound=TEST_FINISHED_AT_UPPER_BOUND,
    )
    client.list_run_artifacts(run_id=TEST_RUN_ID)
    client.get_account_details()

    assert len(all_api_mocks.calls) == 11
    assert_rest_api_call(call=all_api_mocks.calls[0], endpoint="jobs", method="GET")
    assert_rest_api_call(call=all_api_mocks.calls[1], endpoint="jobs", method="POST")
    assert_rest_api_call(
        call=all_api_mocks.calls[2], endpoint=f"jobs/{TEST_JOB_ID}/run", method="POST"
    )
    assert_rest_api_call(call=all_api_mocks.calls[3], endpoint=f"runs/{TEST_RUN_ID}", method="GET")
    assert_rest_api_call(
        call=all_api_mocks.calls[4],
        endpoint=f"runs/{TEST_RUN_ID}/artifacts/manifest.json",
        method="GET",
    )
    assert_rest_api_call(
        call=all_api_mocks.calls[5],
        endpoint=f"runs/{TEST_RUN_ID}/artifacts/run_results.json",
        method="GET",
    )
    assert_rest_api_call(
        call=all_api_mocks.calls[6], endpoint=f"projects/{TEST_PROJECT_ID}", method="GET"
    )
    assert_rest_api_call(
        call=all_api_mocks.calls[7], endpoint=f"environments/{TEST_ENVIRONMENT_ID}", method="GET"
    )
    assert_rest_api_call(call=all_api_mocks.calls[8], endpoint="runs", method="GET")
    assert_rest_api_call(
        call=all_api_mocks.calls[9], endpoint=f"runs/{TEST_RUN_ID}/artifacts", method="GET"
    )
    assert_rest_api_call(call=all_api_mocks.calls[10], endpoint=None, method="GET")


def test_get_or_create_dagster_adhoc_job(
    workspace: DbtCloudWorkspace,
    job_api_mocks: responses.RequestsMock,
) -> None:
    # The expected job name is not in the initial list of jobs so a job is created
    job = workspace._get_or_create_dagster_adhoc_job()  # noqa

    assert len(job_api_mocks.calls) == 4
    assert_rest_api_call(
        call=job_api_mocks.calls[0], endpoint=f"projects/{TEST_PROJECT_ID}", method="GET"
    )
    assert_rest_api_call(
        call=job_api_mocks.calls[1], endpoint=f"environments/{TEST_ENVIRONMENT_ID}", method="GET"
    )
    assert_rest_api_call(call=job_api_mocks.calls[2], endpoint="jobs", method="GET")
    assert_rest_api_call(call=job_api_mocks.calls[3], endpoint="jobs", method="POST")

    assert job.id == TEST_JOB_ID
    assert job.name == TEST_DEFAULT_ADHOC_JOB_NAME
    assert job.account_id == TEST_ACCOUNT_ID
    assert job.project_id == TEST_PROJECT_ID
    assert job.environment_id == TEST_ENVIRONMENT_ID


def test_custom_adhoc_job_name(
    credentials: DbtCloudCredentials,
    job_api_mocks: responses.RequestsMock,
) -> None:
    # Create a workspace with custom ad hoc job name
    workspace = DbtCloudWorkspace(
        credentials=credentials,
        project_id=TEST_PROJECT_ID,
        environment_id=TEST_ENVIRONMENT_ID,
        adhoc_job_name="test_adhoc_job_name",
    )

    job_api_mocks.replace(
        method_or_response=responses.POST,
        url=f"{TEST_REST_API_BASE_URL}/jobs",
        json=SAMPLE_CUSTOM_CREATE_JOB_RESPONSE,
        status=201,
    )
    # We don't fetch the project name and environment name when we use an ad hoc job name.
    job_api_mocks.remove(
        method_or_response=responses.GET,
        url=f"{TEST_REST_API_BASE_URL}/projects/{TEST_PROJECT_ID}",
    )
    job_api_mocks.remove(
        method_or_response=responses.GET,
        url=f"{TEST_REST_API_BASE_URL}/environments/{TEST_ENVIRONMENT_ID}",
    )

    # The expected job name is not in the initial list of jobs so a job is created
    job = workspace._get_or_create_dagster_adhoc_job()  # noqa

    assert len(job_api_mocks.calls) == 2
    assert_rest_api_call(call=job_api_mocks.calls[0], endpoint="jobs", method="GET")
    assert_rest_api_call(call=job_api_mocks.calls[1], endpoint="jobs", method="POST")

    assert job.id == TEST_JOB_ID
    assert job.name == TEST_CUSTOM_ADHOC_JOB_NAME
    assert job.account_id == TEST_ACCOUNT_ID
    assert job.project_id == TEST_PROJECT_ID
    assert job.environment_id == TEST_ENVIRONMENT_ID


@pytest.mark.parametrize(
    "n_polls, last_status, succeed_at_end",
    [
        (0, int(DbtCloudJobRunStatusType.SUCCESS), True),
        (0, int(DbtCloudJobRunStatusType.ERROR), False),
        (0, int(DbtCloudJobRunStatusType.CANCELLED), False),
        (4, int(DbtCloudJobRunStatusType.SUCCESS), True),
        (4, int(DbtCloudJobRunStatusType.ERROR), False),
        (4, int(DbtCloudJobRunStatusType.CANCELLED), False),
        (30, int(DbtCloudJobRunStatusType.SUCCESS), True),
    ],
    ids=[
        "poll_short_success",
        "poll_short_error",
        "poll_short_cancelled",
        "poll_medium_success",
        "poll_medium_error",
        "poll_medium_cancelled",
        "poll_long_success",
    ],
)
def test_poll_run(n_polls, last_status, succeed_at_end, workspace: DbtCloudWorkspace):
    client = workspace.get_client()

    # Create mock responses to mock full poll behavior, used only in this test
    def _mock_interaction():
        with responses.RequestsMock() as response:
            # n polls before updating
            for _ in range(n_polls):
                # TODO parametrize status
                response.add(
                    method=responses.GET,
                    url=f"{TEST_REST_API_BASE_URL}/runs/{TEST_RUN_ID}",
                    json=get_sample_run_response(run_status=int(DbtCloudJobRunStatusType.RUNNING)),
                    status=200,
                )
            # final state will be updated
            response.add(
                method=responses.GET,
                url=f"{TEST_REST_API_BASE_URL}/runs/{TEST_RUN_ID}",
                json=get_sample_run_response(run_status=last_status),
                status=200,
            )

            return client.poll_run(TEST_RUN_ID, poll_interval=0.1)

    if succeed_at_end:
        assert (
            _mock_interaction()
            == get_sample_run_response(run_status=int(DbtCloudJobRunStatusType.SUCCESS))["data"]
        )
    else:
        with pytest.raises(Failure, match="failed!"):
            _mock_interaction()
