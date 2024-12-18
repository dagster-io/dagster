import json
from datetime import datetime
from typing import Optional
from unittest import mock

import pytest
import responses
from dagster import Failure
from dagster_airbyte import AirbyteCloudWorkspace
from dagster_airbyte.resources import (
    AIRBYTE_CONFIGURATION_API_BASE,
    AIRBYTE_CONFIGURATION_API_VERSION,
    AIRBYTE_REST_API_BASE,
    AIRBYTE_REST_API_VERSION,
)
from dagster_airbyte.translator import AirbyteJobStatusType
from dagster_airbyte.types import AirbyteOutput

from dagster_airbyte_tests.experimental.conftest import (
    SAMPLE_CONNECTION_DETAILS,
    TEST_ACCESS_TOKEN,
    TEST_CLIENT_ID,
    TEST_CLIENT_SECRET,
    TEST_CONNECTION_ID,
    TEST_DESTINATION_ID,
    TEST_JOB_ID,
    TEST_UNRECOGNIZED_AIRBYTE_JOB_STATUS_TYPE,
    TEST_WORKSPACE_ID,
    get_job_details_sample,
)


def assert_token_call_and_split_calls(calls: responses.CallList):
    access_token_call = calls[0]
    assert "Authorization" not in access_token_call.request.headers
    access_token_call_body = json.loads(access_token_call.request.body.decode("utf-8"))
    assert access_token_call_body["client_id"] == TEST_CLIENT_ID
    assert access_token_call_body["client_secret"] == TEST_CLIENT_SECRET
    assert (
        access_token_call.request.url
        == f"{AIRBYTE_REST_API_BASE}/{AIRBYTE_REST_API_VERSION}/applications/token"
    )
    return calls[1:]


def assert_rest_api_call(
    call: responses.Call,
    endpoint: str,
    object_id: Optional[str] = None,
    method: Optional[str] = None,
):
    rest_api_url = call.request.url.split("?")[0]
    assert rest_api_url == f"{AIRBYTE_REST_API_BASE}/{AIRBYTE_REST_API_VERSION}/{endpoint}"
    if object_id:
        assert object_id in call.request.body.decode()
    if method:
        assert method == call.request.method
    assert call.request.headers["Authorization"] == f"Bearer {TEST_ACCESS_TOKEN}"


def assert_configuration_api_call(
    call: responses.Call, endpoint: str, object_id: Optional[str] = None
):
    assert (
        call.request.url
        == f"{AIRBYTE_CONFIGURATION_API_BASE}/{AIRBYTE_CONFIGURATION_API_VERSION}/{endpoint}"
    )
    if object_id:
        assert object_id in call.request.body.decode()
    assert call.request.headers["Authorization"] == f"Bearer {TEST_ACCESS_TOKEN}"


def test_refresh_access_token(base_api_mocks: responses.RequestsMock) -> None:
    """Tests the `AirbyteCloudClient._make_request` method and how the API access token is refreshed.

    Args:
        base_api_mocks (responses.RequestsMock): The mock responses for the base API requests,
        i.e. generating the access token.
    """
    resource = AirbyteCloudWorkspace(
        workspace_id=TEST_WORKSPACE_ID,
        client_id=TEST_CLIENT_ID,
        client_secret=TEST_CLIENT_SECRET,
    )
    client = resource.get_client()

    base_api_mocks.add(
        method=responses.GET,
        url=f"{client.rest_api_base_url}/test",
        json={},
        status=200,
    )

    test_time_first_call = datetime(2024, 1, 1, 0, 0, 0)
    test_time_before_expiration = datetime(2024, 1, 1, 0, 2, 0)
    test_time_after_expiration = datetime(2024, 1, 1, 0, 3, 0)
    with mock.patch("dagster_airbyte.resources.datetime", wraps=datetime) as dt:
        # Test first call, must get the access token before calling the jobs api
        dt.now.return_value = test_time_first_call
        client._make_request(method="GET", endpoint="test", base_url=client.rest_api_base_url)  # noqa

        assert len(base_api_mocks.calls) == 2
        api_calls = assert_token_call_and_split_calls(calls=base_api_mocks.calls)

        assert len(api_calls) == 1
        assert_rest_api_call(call=api_calls[0], endpoint="test")

        base_api_mocks.calls.reset()

        # Test second call, occurs before the access token expiration, only the jobs api is called
        dt.now.return_value = test_time_before_expiration
        client._make_request(method="GET", endpoint="test", base_url=client.rest_api_base_url)  # noqa

        assert len(base_api_mocks.calls) == 1
        assert_rest_api_call(call=base_api_mocks.calls[0], endpoint="test")

        base_api_mocks.calls.reset()

        # Test third call, occurs after the token expiration,
        # must refresh the access token before calling the jobs api
        dt.now.return_value = test_time_after_expiration
        client._make_request(method="GET", endpoint="test", base_url=client.rest_api_base_url)  # noqa

        assert len(base_api_mocks.calls) == 2
        api_calls = assert_token_call_and_split_calls(calls=base_api_mocks.calls)

        assert len(api_calls) == 1
        assert_rest_api_call(call=api_calls[0], endpoint="test")


def test_basic_resource_request(
    all_api_mocks: responses.RequestsMock,
) -> None:
    resource = AirbyteCloudWorkspace(
        workspace_id=TEST_WORKSPACE_ID,
        client_id=TEST_CLIENT_ID,
        client_secret=TEST_CLIENT_SECRET,
    )
    client = resource.get_client()

    # fetch workspace data calls
    client.get_connections()
    client.get_connection_details(connection_id=TEST_CONNECTION_ID)
    client.get_destination_details(destination_id=TEST_DESTINATION_ID)
    client.start_sync_job(connection_id=TEST_CONNECTION_ID)
    client.get_job_details(job_id=TEST_JOB_ID)
    client.cancel_job(job_id=TEST_JOB_ID)

    assert len(all_api_mocks.calls) == 7
    # The first call is to create the access token
    api_calls = assert_token_call_and_split_calls(calls=all_api_mocks.calls)
    # The next calls are actual API calls
    assert_rest_api_call(call=api_calls[0], endpoint="connections")
    assert_configuration_api_call(
        call=api_calls[1], endpoint="connections/get", object_id=TEST_CONNECTION_ID
    )
    assert_rest_api_call(call=api_calls[2], endpoint=f"destinations/{TEST_DESTINATION_ID}")
    assert_rest_api_call(call=api_calls[3], endpoint="jobs", object_id=TEST_CONNECTION_ID)
    assert_rest_api_call(call=api_calls[4], endpoint=f"jobs/{TEST_JOB_ID}")
    assert_rest_api_call(call=api_calls[5], endpoint=f"jobs/{TEST_JOB_ID}")


@pytest.mark.parametrize(
    "status",
    [
        AirbyteJobStatusType.SUCCEEDED,
        AirbyteJobStatusType.CANCELLED,
        AirbyteJobStatusType.ERROR,
        AirbyteJobStatusType.FAILED,
        TEST_UNRECOGNIZED_AIRBYTE_JOB_STATUS_TYPE,
    ],
    ids=[
        "job_status_succeeded",
        "job_status_cancelled",
        "job_status_error",
        "job_status_failed",
        "job_status_unrecognized",
    ],
)
def test_airbyte_sync_and_poll_client_job_status(
    status: str, base_api_mocks: responses.RequestsMock
) -> None:
    resource = AirbyteCloudWorkspace(
        workspace_id=TEST_WORKSPACE_ID,
        client_id=TEST_CLIENT_ID,
        client_secret=TEST_CLIENT_SECRET,
    )
    client = resource.get_client()

    test_job_endpoint = f"jobs/{TEST_JOB_ID}"
    test_job_api_url = f"{AIRBYTE_REST_API_BASE}/{AIRBYTE_REST_API_VERSION}/{test_job_endpoint}"

    # Create mock responses to mock full sync and poll behavior to test statuses, used only in this test
    base_api_mocks.add(
        method=responses.POST,
        url=f"{AIRBYTE_REST_API_BASE}/{AIRBYTE_REST_API_VERSION}/jobs",
        json=get_job_details_sample(status=AirbyteJobStatusType.PENDING),
        status=200,
    )
    base_api_mocks.add(
        method=responses.GET,
        url=test_job_api_url,
        json=get_job_details_sample(status=status),
        status=200,
    )
    base_api_mocks.add(
        method=responses.POST,
        url=f"{AIRBYTE_CONFIGURATION_API_BASE}/{AIRBYTE_CONFIGURATION_API_VERSION}/connections/get",
        json=SAMPLE_CONNECTION_DETAILS,
        status=200,
    )

    if status == TEST_UNRECOGNIZED_AIRBYTE_JOB_STATUS_TYPE:
        base_api_mocks.add(
            method=responses.DELETE,
            url=test_job_api_url,
            status=200,
            json=get_job_details_sample(status=AirbyteJobStatusType.CANCELLED),
        )

    if status in [AirbyteJobStatusType.ERROR, AirbyteJobStatusType.FAILED]:
        with pytest.raises(Failure, match="Job failed"):
            client.sync_and_poll(connection_id=TEST_CONNECTION_ID, poll_interval=0)

    elif status == AirbyteJobStatusType.CANCELLED:
        with pytest.raises(Failure, match="Job was cancelled"):
            client.sync_and_poll(connection_id=TEST_CONNECTION_ID, poll_interval=0)

    elif status == TEST_UNRECOGNIZED_AIRBYTE_JOB_STATUS_TYPE:
        with pytest.raises(Failure, match="unexpected state"):
            client.sync_and_poll(connection_id=TEST_CONNECTION_ID, poll_interval=0)
        assert_rest_api_call(
            call=base_api_mocks.calls[-1], endpoint=test_job_endpoint, method=responses.DELETE
        )

    else:
        result = client.sync_and_poll(connection_id=TEST_CONNECTION_ID, poll_interval=0)
        assert result == AirbyteOutput(
            job_details=get_job_details_sample(AirbyteJobStatusType.SUCCEEDED),
            connection_details=SAMPLE_CONNECTION_DETAILS,
        )


@pytest.mark.parametrize(
    "n_polls, succeed_at_end",
    [
        (0, True),
        (0, False),
        (4, True),
        (4, False),
        (30, True),
    ],
    ids=[
        "sync_short_success",
        "sync_short_failure",
        "sync_medium_success",
        "sync_medium_failure",
        "sync_long_success",
    ],
)
def test_airbyte_sync_and_poll_client_poll_process(
    n_polls, succeed_at_end, base_api_mocks: responses.RequestsMock
):
    resource = AirbyteCloudWorkspace(
        workspace_id=TEST_WORKSPACE_ID,
        client_id=TEST_CLIENT_ID,
        client_secret=TEST_CLIENT_SECRET,
    )
    client = resource.get_client()

    # Create mock responses to mock full sync and poll behavior, used only in this test
    def _mock_interaction():
        # initial state
        base_api_mocks.add(
            method=responses.POST,
            url=f"{AIRBYTE_REST_API_BASE}/{AIRBYTE_REST_API_VERSION}/jobs",
            json=get_job_details_sample(status=AirbyteJobStatusType.PENDING),
            status=200,
        )
        base_api_mocks.add(
            method=responses.POST,
            url=f"{AIRBYTE_CONFIGURATION_API_BASE}/{AIRBYTE_CONFIGURATION_API_VERSION}/connections/get",
            json=SAMPLE_CONNECTION_DETAILS,
            status=200,
        )
        # n polls before updating
        for _ in range(n_polls):
            base_api_mocks.add(
                method=responses.GET,
                url=f"{AIRBYTE_REST_API_BASE}/{AIRBYTE_REST_API_VERSION}/jobs/{TEST_JOB_ID}",
                json=get_job_details_sample(status=AirbyteJobStatusType.RUNNING),
                status=200,
            )
        # final state will be updated
        base_api_mocks.add(
            method=responses.GET,
            url=f"{AIRBYTE_REST_API_BASE}/{AIRBYTE_REST_API_VERSION}/jobs/{TEST_JOB_ID}",
            json=get_job_details_sample(
                status=AirbyteJobStatusType.SUCCEEDED
                if succeed_at_end
                else AirbyteJobStatusType.FAILED
            ),
            status=200,
        )
        return client.sync_and_poll(connection_id=TEST_CONNECTION_ID, poll_interval=0.1)

    if succeed_at_end:
        assert _mock_interaction() == AirbyteOutput(
            job_details=get_job_details_sample(AirbyteJobStatusType.SUCCEEDED),
            connection_details=SAMPLE_CONNECTION_DETAILS,
        )
    else:
        with pytest.raises(Failure, match="Job failed"):
            _mock_interaction()


@pytest.mark.parametrize(
    "cancel_on_termination",
    [
        True,
        False,
    ],
    ids=[
        "cancel_on_termination_true",
        "cancel_on_termination_false",
    ],
)
def test_airbyte_sync_and_poll_client_cancel_on_termination(
    cancel_on_termination: bool, base_api_mocks: responses.RequestsMock
) -> None:
    resource = AirbyteCloudWorkspace(
        workspace_id=TEST_WORKSPACE_ID,
        client_id=TEST_CLIENT_ID,
        client_secret=TEST_CLIENT_SECRET,
    )
    client = resource.get_client()

    test_job_endpoint = f"jobs/{TEST_JOB_ID}"
    test_job_api_url = f"{AIRBYTE_REST_API_BASE}/{AIRBYTE_REST_API_VERSION}/{test_job_endpoint}"

    # Create mock responses to mock full sync and poll behavior to test statuses, used only in this test
    base_api_mocks.add(
        method=responses.POST,
        url=f"{AIRBYTE_REST_API_BASE}/{AIRBYTE_REST_API_VERSION}/jobs",
        json=get_job_details_sample(status=AirbyteJobStatusType.PENDING),
        status=200,
    )
    base_api_mocks.add(
        method=responses.GET,
        url=test_job_api_url,
        json=get_job_details_sample(status=TEST_UNRECOGNIZED_AIRBYTE_JOB_STATUS_TYPE),
        status=200,
    )
    base_api_mocks.add(
        method=responses.POST,
        url=f"{AIRBYTE_CONFIGURATION_API_BASE}/{AIRBYTE_CONFIGURATION_API_VERSION}/connections/get",
        json=SAMPLE_CONNECTION_DETAILS,
        status=200,
    )

    if cancel_on_termination:
        base_api_mocks.add(
            method=responses.DELETE,
            url=test_job_api_url,
            status=200,
            json=get_job_details_sample(status=AirbyteJobStatusType.CANCELLED),
        )

    with pytest.raises(Failure, match="unexpected state"):
        client.sync_and_poll(
            connection_id=TEST_CONNECTION_ID,
            poll_interval=0,
            cancel_on_termination=cancel_on_termination,
        )
    if cancel_on_termination:
        assert_rest_api_call(
            call=base_api_mocks.calls[-1], endpoint=test_job_endpoint, method=responses.DELETE
        )
    else:
        # If we don't cancel on termination, the last call will be a call to fetch the job details
        assert_rest_api_call(
            call=base_api_mocks.calls[-1], endpoint=test_job_endpoint, method=responses.GET
        )
