from typing import Optional

import pytest
import responses
from dagster import Failure
from dagster_dbt.cloud.resources import DbtCloudWorkspace
from dagster_dbt.cloud.types import DbtCloudJobRunStatusType

from dagster_dbt_tests.cloud.preview.conftest import (
    TEST_ACCOUNT_ID,
    TEST_ADHOC_JOB_NAME,
    TEST_ENVIRONMENT_ID,
    TEST_JOB_ID,
    TEST_PROJECT_ID,
    TEST_REST_API_BASE_URL,
    TEST_RUN_ID,
    TEST_TOKEN,
    get_sample_run_response,
)


def assert_rest_api_call(
    call: responses.Call,
    endpoint: str,
    method: Optional[str] = None,
):
    rest_api_url = call.request.url.split("?")[0]
    assert rest_api_url == f"{TEST_REST_API_BASE_URL}/{endpoint}"
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
        project_id=TEST_PROJECT_ID, environment_id=TEST_ENVIRONMENT_ID, job_name=TEST_ADHOC_JOB_NAME
    )
    client.trigger_job_run(job_id=TEST_JOB_ID)
    client.get_run_details(run_id=TEST_RUN_ID)

    assert len(all_api_mocks.calls) == 4
    assert_rest_api_call(call=all_api_mocks.calls[0], endpoint="jobs", method="GET")
    assert_rest_api_call(call=all_api_mocks.calls[1], endpoint="jobs", method="POST")
    assert_rest_api_call(call=all_api_mocks.calls[2], endpoint=f"jobs/{TEST_JOB_ID}/run", method="POST")
    assert_rest_api_call(call=all_api_mocks.calls[3], endpoint=f"runs/{TEST_RUN_ID}", method="GET")


def test_get_or_create_dagster_adhoc_job(
    workspace: DbtCloudWorkspace,
    job_api_mocks: responses.RequestsMock,
) -> None:
    # The expected job name is not in the initial list of jobs so a job is created
    job = workspace._get_or_create_dagster_adhoc_job()  # noqa

    assert len(job_api_mocks.calls) == 2
    assert_rest_api_call(call=job_api_mocks.calls[0], endpoint="jobs", method="GET")
    assert_rest_api_call(call=job_api_mocks.calls[1], endpoint="jobs", method="POST")

    assert job.id == TEST_JOB_ID
    assert job.name == TEST_ADHOC_JOB_NAME
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
