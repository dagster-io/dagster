import json
from datetime import datetime
from typing import Optional
from unittest import mock

import responses
from dagster_airbyte import AirbyteCloudWorkspace
from dagster_airbyte.resources import (
    AIRBYTE_CONFIGURATION_API_BASE,
    AIRBYTE_CONFIGURATION_API_VERSION,
    AIRBYTE_REST_API_BASE,
    AIRBYTE_REST_API_VERSION,
)

from dagster_airbyte_tests.experimental.conftest import (
    TEST_ACCESS_TOKEN,
    TEST_CLIENT_ID,
    TEST_CLIENT_SECRET,
    TEST_CONNECTION_ID,
    TEST_DESTINATION_ID,
    TEST_JOB_ID,
    TEST_WORKSPACE_ID,
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


def assert_rest_api_call(call: responses.Call, endpoint: str, object_id: Optional[str] = None):
    rest_api_url = call.request.url.split("?")[0]
    assert rest_api_url == f"{AIRBYTE_REST_API_BASE}/{AIRBYTE_REST_API_VERSION}/{endpoint}"
    if object_id:
        assert object_id in call.request.body.decode()
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
