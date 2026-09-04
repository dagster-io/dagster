import datetime
import json
import re
from unittest import mock

import pytest
import responses
from dagster import Failure
from dagster_airbyte import AirbyteCloudResource, AirbyteJobStatusType, AirbyteOutput
from dagster_airbyte.resources import AirbyteClient


@responses.activate
def test_trigger_connection() -> None:
    ab_resource = AirbyteCloudResource(
        client_id="some_client_id", client_secret="some_client_secret", poll_interval=0
    )
    responses.add(
        responses.POST,
        f"{ab_resource.api_base_url}/applications/token",
        json={"access_token": "some_access_token"},
    )
    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/jobs",
        json={"jobId": 1, "status": "pending", "jobType": "sync"},
        status=200,
    )
    resp = ab_resource.start_sync("some_connection")
    assert resp == {"job": {"id": 1, "status": "pending"}}


@responses.activate
def test_trigger_connection_fail() -> None:
    ab_resource = AirbyteCloudResource(
        client_id="some_client_id", client_secret="some_client_secret"
    )
    responses.add(
        responses.POST,
        f"{ab_resource.api_base_url}/applications/token",
        json={"access_token": "some_access_token"},
    )

    with pytest.raises(
        Failure,
        match=re.escape("Max retries (3) exceeded with url: https://api.airbyte.com/v1/jobs."),
    ):
        ab_resource.sync_and_poll("some_connection")


@responses.activate
@pytest.mark.parametrize(
    "state",
    [
        AirbyteJobStatusType.SUCCEEDED,
        AirbyteJobStatusType.CANCELLED,
        AirbyteJobStatusType.ERROR,
        "unrecognized",
    ],
)
def test_sync_and_poll(state) -> None:
    ab_resource = AirbyteCloudResource(
        client_id="some_client_id", client_secret="some_client_secret", poll_interval=0
    )

    responses.add(
        responses.POST,
        f"{ab_resource.api_base_url}/applications/token",
        json={"access_token": "some_access_token"},
    )
    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/jobs",
        json={"jobId": 1, "status": "pending", "jobType": "sync"},
        status=200,
    )
    responses.add(
        method=responses.GET,
        url=ab_resource.api_base_url + "/jobs/1",
        json={"jobId": 1, "status": state, "jobType": "sync"},
        status=200,
    )

    if state == "unrecognized":
        responses.add(
            responses.DELETE,
            f"{ab_resource.api_base_url}/jobs/1",
            status=200,
            json={"jobId": 1, "status": "cancelled", "jobType": "sync"},
        )

    if state == AirbyteJobStatusType.ERROR:
        with pytest.raises(Failure, match="Job failed"):
            ab_resource.sync_and_poll("some_connection", 0)

    elif state == AirbyteJobStatusType.CANCELLED:
        with pytest.raises(Failure, match="Job was cancelled"):
            ab_resource.sync_and_poll("some_connection", 0)

    elif state == "unrecognized":
        with pytest.raises(Failure, match="unexpected state"):
            ab_resource.sync_and_poll("some_connection", 0)

    else:
        result = ab_resource.sync_and_poll("some_connection", 0)
        assert result == AirbyteOutput(
            job_details={"job": {"id": 1, "status": state}},
            connection_details={},
        )


@responses.activate
def test_start_sync_bad_out_fail() -> None:
    ab_resource = AirbyteCloudResource(
        client_id="some_client_id", client_secret="some_client_secret", poll_interval=0
    )

    responses.add(
        responses.POST,
        f"{ab_resource.api_base_url}/applications/token",
        json={"access_token": "some_access_token"},
    )
    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/jobs",
        json=None,
        status=500,
    )
    with pytest.raises(
        Failure,
        match=re.escape("Max retries (3) exceeded with url: https://api.airbyte.com/v1/jobs."),
    ):
        ab_resource.start_sync("some_connection")


@responses.activate
def test_refresh_access_token() -> None:
    ab_resource = AirbyteCloudResource(
        client_id="some_client_id", client_secret="some_client_secret", poll_interval=0
    )
    responses.add(
        responses.POST,
        f"{ab_resource.api_base_url}/applications/token",
        json={"access_token": "some_access_token"},
    )
    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/jobs",
        json={"jobId": 1, "status": "pending", "jobType": "sync"},
        status=200,
    )

    test_time_first_call = datetime.datetime(2024, 1, 1, 0, 0, 0)
    test_time_before_expiration = datetime.datetime(2024, 1, 1, 0, 2, 0)
    test_time_after_expiration = datetime.datetime(2024, 1, 1, 0, 3, 0)
    with mock.patch("dagster_airbyte.legacy_resources.datetime", wraps=datetime.datetime) as dt:
        # Test first call, must get the access token before calling the jobs api
        dt.now.return_value = test_time_first_call
        ab_resource.start_sync("some_connection")

        assert len(responses.calls) == 2
        access_token_call = responses.calls[0]
        jobs_api_call = responses.calls[1]

        assert "Authorization" not in access_token_call.request.headers
        access_token_call_body = json.loads(access_token_call.request.body.decode("utf-8"))
        assert access_token_call_body["client_id"] == "some_client_id"
        assert access_token_call_body["client_secret"] == "some_client_secret"
        assert jobs_api_call.request.headers["Authorization"] == "Bearer some_access_token"

        responses.calls.reset()

        # Test second call, occurs before the access token expiration, only the jobs api is called
        dt.now.return_value = test_time_before_expiration
        ab_resource.start_sync("some_connection")

        assert len(responses.calls) == 1
        jobs_api_call = responses.calls[0]

        assert jobs_api_call.request.headers["Authorization"] == "Bearer some_access_token"

        responses.calls.reset()

        # Test third call, occurs after the token expiration,
        # must refresh the access token before calling the jobs api
        dt.now.return_value = test_time_after_expiration
        ab_resource.start_sync("some_connection")

        assert len(responses.calls) == 2
        access_token_call = responses.calls[0]
        jobs_api_call = responses.calls[1]

        assert "Authorization" not in access_token_call.request.headers
        access_token_call_body = json.loads(access_token_call.request.body.decode("utf-8"))
        assert access_token_call_body["client_id"] == "some_client_id"
        assert access_token_call_body["client_secret"] == "some_client_secret"
        assert jobs_api_call.request.headers["Authorization"] == "Bearer some_access_token"


# ── Regression tests for https://github.com/dagster-io/dagster/issues/34172 ──
# AirbyteClient._single_request must NOT retry 4xx client errors.


@responses.activate
def test_single_request_does_not_retry_4xx() -> None:
    """A 4xx response must raise Failure immediately without retrying."""
    client = AirbyteClient(
        workspace_id="test-workspace",
        client_id="test-client-id",
        client_secret="test-client-secret",
        request_max_retries=3,
        request_retry_delay=0,
        request_timeout=15,
    )

    # Mock the token endpoint so _get_session() succeeds
    responses.add(
        responses.POST,
        f"{client.rest_api_base_url}/applications/token",
        json={"access_token": "test-token"},
        status=200,
    )
    responses.add(
        responses.POST,
        f"{client.rest_api_base_url}/test-endpoint",
        json={"error": "bad request"},
        status=400,
    )

    with pytest.raises(Failure) as exc_info:
        client._single_request("POST", f"{client.rest_api_base_url}/test-endpoint", data={})

    # Must have raised on the first attempt — only 2 calls (1 token + 1 request), not 5
    request_calls = [c for c in responses.calls if "test-endpoint" in c.request.url]
    assert len(request_calls) == 1, (
        f"Expected 1 request call (no retries on 4xx), got {len(request_calls)}"
    )
    assert "400" in str(exc_info.value)


@responses.activate
def test_single_request_retries_5xx() -> None:
    """A 5xx response IS transient and must be retried up to request_max_retries times."""
    client = AirbyteClient(
        workspace_id="test-workspace",
        client_id="test-client-id",
        client_secret="test-client-secret",
        request_max_retries=2,
        request_retry_delay=0,
        request_timeout=15,
    )

    # Token endpoint (called once per session)
    responses.add(
        responses.POST,
        f"{client.rest_api_base_url}/applications/token",
        json={"access_token": "test-token"},
        status=200,
    )
    # All 3 attempts return 503
    for _ in range(3):
        responses.add(
            responses.GET,
            f"{client.rest_api_base_url}/health",
            json={"error": "service unavailable"},
            status=503,
        )

    with pytest.raises(Failure) as exc_info:
        client._single_request("GET", f"{client.rest_api_base_url}/health")

    health_calls = [c for c in responses.calls if "health" in c.request.url]
    assert len(health_calls) == 3, (
        f"Expected 3 calls (1 + 2 retries on 5xx), got {len(health_calls)}"
    )
    assert "Max retries" in str(exc_info.value)
