import logging

import pytest
import responses
from dagster import Failure
from dagster_dbt.cloud_v2.client import DbtCloudWorkspaceClient

from dagster_dbt_tests.cloud_v2.conftest import (
    TEST_ACCESS_URL,
    TEST_ACCOUNT_ID,
    TEST_ADHOC_JOB_ID,
    TEST_REST_API_BASE_URL,
    TEST_TOKEN,
)


def build_client(access_url: str = TEST_ACCESS_URL) -> DbtCloudWorkspaceClient:
    return DbtCloudWorkspaceClient(
        account_id=TEST_ACCOUNT_ID,
        token=TEST_TOKEN,
        access_url=access_url,
        request_max_retries=1,
        request_retry_delay=0,
        request_timeout=1,
    )


def test_api_v2_url_strips_trailing_slash() -> None:
    assert build_client().api_v2_url == TEST_REST_API_BASE_URL
    # Single-tenant access URLs are often configured with a trailing slash; a
    # naive join would produce a `//api/v2` path that dbt Cloud's edge 404s.
    assert build_client(f"{TEST_ACCESS_URL}/").api_v2_url == TEST_REST_API_BASE_URL


@responses.activate
def test_destroy_job() -> None:
    client = build_client()

    # Successful delete returns the parsed payload.
    responses.add(
        method=responses.DELETE,
        url=f"{TEST_REST_API_BASE_URL}/jobs/{TEST_ADHOC_JOB_ID}",
        json={"data": {"id": TEST_ADHOC_JOB_ID}},
        status=200,
    )
    assert client.destroy_job(TEST_ADHOC_JOB_ID) == {"id": TEST_ADHOC_JOB_ID}

    # A 404 means the job is already gone — treated as success, no retry.
    responses.reset()
    responses.add(
        method=responses.DELETE,
        url=f"{TEST_REST_API_BASE_URL}/jobs/{TEST_ADHOC_JOB_ID}",
        json={"status": {"user_message": "Not found"}},
        status=404,
    )
    assert client.destroy_job(TEST_ADHOC_JOB_ID) is None
    assert len(responses.calls) == 1

    # Other error statuses still raise after retries.
    responses.reset()
    responses.add(
        method=responses.DELETE,
        url=f"{TEST_REST_API_BASE_URL}/jobs/{TEST_ADHOC_JOB_ID}",
        json={"status": {"user_message": "Server error"}},
        status=500,
    )
    with pytest.raises(Failure, match="Max retries"):
        client.destroy_job(TEST_ADHOC_JOB_ID)
    assert len(responses.calls) == 2  # initial attempt + 1 retry


@responses.activate
def test_request_error_logs_response_body(caplog: pytest.LogCaptureFixture) -> None:
    client = build_client()
    responses.add(
        method=responses.POST,
        url=f"{TEST_REST_API_BASE_URL}/jobs/{TEST_ADHOC_JOB_ID}/run",
        json={"status": {"user_message": "Invalid dbt commands"}},
        status=400,
    )
    with caplog.at_level(logging.ERROR, logger="dagster"):
        with pytest.raises(Failure, match="Max retries"):
            client.trigger_job_run(job_id=TEST_ADHOC_JOB_ID)
    assert "Invalid dbt commands" in caplog.text
