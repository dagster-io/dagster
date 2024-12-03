import json
from datetime import datetime
from unittest import mock

import responses
from dagster_airbyte import AirbyteCloudWorkspace

from dagster_airbyte_tests.experimental.conftest import (
    TEST_ACCESS_TOKEN,
    TEST_CLIENT_ID,
    TEST_CLIENT_SECRET,
    TEST_WORKSPACE_ID,
)


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
        url=f"{client.api_base_url}/test",
        json={},
        status=200,
    )

    test_time_first_call = datetime(2024, 1, 1, 0, 0, 0)
    test_time_before_expiration = datetime(2024, 1, 1, 0, 2, 0)
    test_time_after_expiration = datetime(2024, 1, 1, 0, 3, 0)
    with mock.patch("dagster_airbyte.resources.datetime", wraps=datetime) as dt:
        # Test first call, must get the access token before calling the jobs api
        dt.now.return_value = test_time_first_call
        client._make_request(method="GET", endpoint="test", base_url=client.api_base_url)  # noqa

        assert len(base_api_mocks.calls) == 2
        access_token_call = base_api_mocks.calls[0]
        jobs_api_call = base_api_mocks.calls[1]

        assert "Authorization" not in access_token_call.request.headers
        access_token_call_body = json.loads(access_token_call.request.body.decode("utf-8"))
        assert access_token_call_body["client_id"] == TEST_CLIENT_ID
        assert access_token_call_body["client_secret"] == TEST_CLIENT_SECRET
        assert jobs_api_call.request.headers["Authorization"] == f"Bearer {TEST_ACCESS_TOKEN}"

        base_api_mocks.calls.reset()

        # Test second call, occurs before the access token expiration, only the jobs api is called
        dt.now.return_value = test_time_before_expiration
        client._make_request(method="GET", endpoint="test", base_url=client.api_base_url)  # noqa

        assert len(base_api_mocks.calls) == 1
        jobs_api_call = base_api_mocks.calls[0]

        assert jobs_api_call.request.headers["Authorization"] == f"Bearer {TEST_ACCESS_TOKEN}"

        base_api_mocks.calls.reset()

        # Test third call, occurs after the token expiration,
        # must refresh the access token before calling the jobs api
        dt.now.return_value = test_time_after_expiration
        client._make_request(method="GET", endpoint="test", base_url=client.api_base_url)  # noqa

        assert len(base_api_mocks.calls) == 2
        access_token_call = base_api_mocks.calls[0]
        jobs_api_call = base_api_mocks.calls[1]

        assert "Authorization" not in access_token_call.request.headers
        access_token_call_body = json.loads(access_token_call.request.body.decode("utf-8"))
        assert access_token_call_body["client_id"] == TEST_CLIENT_ID
        assert access_token_call_body["client_secret"] == TEST_CLIENT_SECRET
        assert jobs_api_call.request.headers["Authorization"] == f"Bearer {TEST_ACCESS_TOKEN}"


def test_basic_resource_request(
    destination_id: str,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    resource = AirbyteCloudWorkspace(
        workspace_id=TEST_WORKSPACE_ID,
        client_id=TEST_CLIENT_ID,
        client_secret=TEST_CLIENT_SECRET,
    )
    client = resource.get_client()

    # fetch workspace data calls
    client.get_connections()
    client.get_destination_details(destination_id=destination_id)

    assert len(fetch_workspace_data_api_mocks.calls) == 3
    # The first call is to create the access token
    assert "Authorization" not in fetch_workspace_data_api_mocks.calls[0].request.headers
    # The two next calls are actual API calls
    assert "connections" in fetch_workspace_data_api_mocks.calls[1].request.url
    assert f"destinations/{destination_id}" in fetch_workspace_data_api_mocks.calls[2].request.url
