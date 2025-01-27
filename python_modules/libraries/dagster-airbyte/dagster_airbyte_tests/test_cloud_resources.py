import datetime
import json
import re
from unittest import mock

import pytest
import responses
from dagster import Failure
from dagster_airbyte import AirbyteCloudResource, AirbyteJobStatusType, AirbyteOutput


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
    with mock.patch("dagster_airbyte.resources.datetime", wraps=datetime.datetime) as dt:
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
