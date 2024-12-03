import json
from datetime import datetime
from unittest import mock

import responses
from dagster_airbyte import AirbyteCloudWorkspace


def test_refresh_access_token(base_api_mocks: responses.RequestsMock) -> None:
    resource = AirbyteCloudWorkspace(
        workspace_id="some_workspace_id",
        client_id="some_client_id",
        client_secret="some_client_secret",
    )
    client = resource.get_client()

    base_api_mocks.add(
        responses.POST,
        f"{client.api_base_url}/applications/token",
        json={"access_token": "some_access_token"},
    )
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
        client._make_request(method="GET", endpoint="/test")  # noqa

        assert len(base_api_mocks.calls) == 2
        access_token_call = base_api_mocks.calls[0]
        jobs_api_call = base_api_mocks.calls[1]

        assert "Authorization" not in access_token_call.request.headers
        access_token_call_body = json.loads(access_token_call.request.body.decode("utf-8"))
        assert access_token_call_body["client_id"] == "some_client_id"
        assert access_token_call_body["client_secret"] == "some_client_secret"
        assert jobs_api_call.request.headers["Authorization"] == "Bearer some_access_token"

        base_api_mocks.calls.reset()

        # Test second call, occurs before the access token expiration, only the jobs api is called
        dt.now.return_value = test_time_before_expiration
        client._make_request(method="GET", endpoint="/test")  # noqa

        assert len(base_api_mocks.calls) == 1
        jobs_api_call = base_api_mocks.calls[0]

        assert jobs_api_call.request.headers["Authorization"] == "Bearer some_access_token"

        base_api_mocks.calls.reset()

        # Test third call, occurs after the token expiration,
        # must refresh the access token before calling the jobs api
        dt.now.return_value = test_time_after_expiration
        client._make_request(method="GET", endpoint="/test")  # noqa

        assert len(base_api_mocks.calls) == 2
        access_token_call = base_api_mocks.calls[0]
        jobs_api_call = base_api_mocks.calls[1]

        assert "Authorization" not in access_token_call.request.headers
        access_token_call_body = json.loads(access_token_call.request.body.decode("utf-8"))
        assert access_token_call_body["client_id"] == "some_client_id"
        assert access_token_call_body["client_secret"] == "some_client_secret"
        assert jobs_api_call.request.headers["Authorization"] == "Bearer some_access_token"
