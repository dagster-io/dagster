from typing import Optional

import responses
from dagster_dbt.cloud.resources import DbtCloudWorkspace

from dagster_dbt_tests.cloud.preview.conftest import (
    TEST_ACCOUNT_ID,
    TEST_ADHOC_JOB_NAME,
    TEST_ENVIRONMENT_ID,
    TEST_JOB_ID,
    TEST_PROJECT_ID,
    TEST_REST_API_BASE_URL,
    TEST_TOKEN,
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
    api_mocks: responses.RequestsMock,
) -> None:
    client = workspace.get_client()

    # jobs data calls
    client.list_jobs(project_id=TEST_PROJECT_ID, environment_id=TEST_ENVIRONMENT_ID)
    client.create_job(
        project_id=TEST_PROJECT_ID, environment_id=TEST_ENVIRONMENT_ID, job_name=TEST_ADHOC_JOB_NAME
    )

    assert len(api_mocks.calls) == 2
    assert_rest_api_call(call=api_mocks.calls[0], endpoint="jobs", method="GET")
    assert_rest_api_call(call=api_mocks.calls[1], endpoint="jobs", method="POST")


def test_get_or_create_dagster_adhoc_job(
    workspace: DbtCloudWorkspace,
    api_mocks: responses.RequestsMock,
) -> None:
    # The expected job name is not in the initial list of jobs so a job is created
    job = workspace._get_or_create_dagster_adhoc_job()  # noqa

    assert len(api_mocks.calls) == 2
    assert_rest_api_call(call=api_mocks.calls[0], endpoint="jobs", method="GET")
    assert_rest_api_call(call=api_mocks.calls[1], endpoint="jobs", method="POST")

    assert job.id == TEST_JOB_ID
    assert job.name == TEST_ADHOC_JOB_NAME
    assert job.account_id == TEST_ACCOUNT_ID
    assert job.project_id == TEST_PROJECT_ID
    assert job.environment_id == TEST_ENVIRONMENT_ID
