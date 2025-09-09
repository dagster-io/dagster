import json
import re
from datetime import datetime
from enum import Enum
from typing import Optional, Union
from unittest.mock import MagicMock, patch

import pytest
import responses
from dagster import AssetExecutionContext, AssetKey, Failure, materialize
from dagster._core.events import DagsterEventType
from dagster_airbyte import AirbyteCloudWorkspace, airbyte_assets
from dagster_airbyte.resources import AirbyteWorkspace
from dagster_airbyte.translator import AirbyteJobStatusType
from dagster_airbyte.types import AirbyteOutput
from dagster_airbyte.utils import clean_name

from dagster_airbyte_tests.beta.conftest import (
    AIRBYTE_OSS_CONFIGURATION_API_BASE_URL,
    AIRBYTE_OSS_REST_API_BASE_URL,
    SAMPLE_ACCESS_TOKEN,
    SAMPLE_CONNECTION_DETAILS,
    TEST_ACCESS_TOKEN,
    TEST_ANOTHER_STREAM_NAME,
    TEST_BASIC_AUTH_B64,
    TEST_CLIENT_ID,
    TEST_CLIENT_SECRET,
    TEST_CONNECTION_ID,
    TEST_DESTINATION_ID,
    TEST_JOB_ID,
    TEST_PASSWORD,
    TEST_STREAM_PREFIX,
    TEST_UNEXPECTED_STREAM_NAME,
    TEST_UNRECOGNIZED_AIRBYTE_JOB_STATUS_TYPE,
    TEST_USERNAME,
    TEST_WORKSPACE_ID,
    get_job_details_sample,
)
from dagster_airbyte_tests.beta.utils import optional_pytest_raise


def assert_token_call_and_split_calls(base_url: str, calls: responses.CallList):
    access_token_call = calls[0]
    assert "Authorization" not in access_token_call.request.headers
    access_token_call_body = json.loads(access_token_call.request.body.decode("utf-8"))
    assert access_token_call_body["client_id"] == TEST_CLIENT_ID
    assert access_token_call_body["client_secret"] == TEST_CLIENT_SECRET
    assert access_token_call.request.url == f"{base_url}/applications/token"
    return calls[1:]


class AuthMethod(Enum):
    NO_AUTH = "no_auth"
    BEARER = "bearer"
    BASIC = "basic"


def assert_api_call(
    call: responses.Call,
    base_url: str,
    endpoint: str,
    object_id: Optional[str] = None,
    method: Optional[str] = None,
    auth_method: AuthMethod = AuthMethod.BEARER,
):
    rest_api_url = call.request.url.split("?")[0]
    assert rest_api_url == f"{base_url}/{endpoint}"
    if object_id:
        assert object_id in call.request.body.decode()
    if method:
        assert method == call.request.method

    if auth_method == AuthMethod.BEARER:
        assert "Authorization" in call.request.headers
        assert call.request.headers["Authorization"] == f"Bearer {TEST_ACCESS_TOKEN}"
    elif auth_method == AuthMethod.BASIC:
        assert "Authorization" in call.request.headers
        assert call.request.headers["Authorization"] == f"Basic {TEST_BASIC_AUTH_B64}"
    else:
        assert "Authorization" not in call.request.headers


def test_refresh_access_token(
    base_api_mocks: responses.RequestsMock,
    resource: Union[AirbyteCloudWorkspace, AirbyteWorkspace],
    rest_api_url: str,
) -> None:
    """Tests the `AirbyteCloudClient._single_request` method and how the API access token is refreshed.

    Args:
        base_api_mocks (responses.RequestsMock): The mock responses for the base API requests,
        i.e. generating the access token.
    """
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
    with patch("dagster_airbyte.resources.datetime", wraps=datetime) as dt:
        # Test first call, must get the access token before calling the jobs api
        dt.now.return_value = test_time_first_call
        client._single_request(method="GET", url=f"{client.rest_api_base_url}/test")  # noqa

        assert len(base_api_mocks.calls) == 2
        api_calls = assert_token_call_and_split_calls(
            base_url=rest_api_url, calls=base_api_mocks.calls
        )

        assert len(api_calls) == 1
        assert_api_call(base_url=rest_api_url, call=api_calls[0], endpoint="test")

        base_api_mocks.calls.reset()

        # Test second call, occurs before the access token expiration, only the jobs api is called
        dt.now.return_value = test_time_before_expiration
        client._single_request(method="GET", url=f"{client.rest_api_base_url}/test")  # noqa

        assert len(base_api_mocks.calls) == 1
        assert_api_call(base_url=rest_api_url, call=base_api_mocks.calls[0], endpoint="test")

        base_api_mocks.calls.reset()

        # Test third call, occurs after the token expiration,
        # must refresh the access token before calling the jobs api
        dt.now.return_value = test_time_after_expiration
        client._single_request(method="GET", url=f"{client.rest_api_base_url}/test")  # noqa

        assert len(base_api_mocks.calls) == 2
        api_calls = assert_token_call_and_split_calls(
            base_url=rest_api_url, calls=base_api_mocks.calls
        )

        assert len(api_calls) == 1
        assert_api_call(base_url=rest_api_url, call=api_calls[0], endpoint="test")


def test_basic_resource_request(
    all_api_mocks: responses.RequestsMock,
    resource: Union[AirbyteCloudWorkspace, AirbyteWorkspace],
    rest_api_url: str,
    config_api_url: str,
) -> None:
    client = resource.get_client()

    # fetch workspace data calls
    client.validate_workspace_id()
    client.get_connections()
    client.get_connection_details(connection_id=TEST_CONNECTION_ID)
    client.get_destination_details(destination_id=TEST_DESTINATION_ID)
    client.start_sync_job(connection_id=TEST_CONNECTION_ID)
    client.get_job_details(job_id=TEST_JOB_ID)
    client.cancel_job(job_id=TEST_JOB_ID)

    assert len(all_api_mocks.calls) == 9
    # The first call is to create the access token
    api_calls = assert_token_call_and_split_calls(base_url=rest_api_url, calls=all_api_mocks.calls)
    # The next calls are actual API calls
    assert_api_call(
        base_url=rest_api_url, call=api_calls[0], endpoint=f"workspaces/{TEST_WORKSPACE_ID}"
    )
    assert_api_call(base_url=rest_api_url, call=api_calls[1], endpoint="connections")
    assert_api_call(
        base_url=config_api_url,
        call=api_calls[3],
        endpoint="connections/get",
        object_id=TEST_CONNECTION_ID,
    )
    assert_api_call(
        base_url=rest_api_url, call=api_calls[4], endpoint=f"destinations/{TEST_DESTINATION_ID}"
    )
    assert_api_call(
        base_url=rest_api_url, call=api_calls[5], endpoint="jobs", object_id=TEST_CONNECTION_ID
    )
    assert_api_call(base_url=rest_api_url, call=api_calls[6], endpoint=f"jobs/{TEST_JOB_ID}")
    assert_api_call(base_url=rest_api_url, call=api_calls[7], endpoint=f"jobs/{TEST_JOB_ID}")


@pytest.mark.parametrize(
    "status, error_expected, exception_message",
    [
        (AirbyteJobStatusType.SUCCEEDED, False, None),
        (AirbyteJobStatusType.CANCELLED, True, "Job was cancelled"),
        (AirbyteJobStatusType.ERROR, True, "Job failed"),
        (AirbyteJobStatusType.FAILED, True, "Job failed"),
        (TEST_UNRECOGNIZED_AIRBYTE_JOB_STATUS_TYPE, True, "unexpected state"),
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
    status: str,
    error_expected: bool,
    exception_message: str,
    base_api_mocks: responses.RequestsMock,
    resource: Union[AirbyteCloudWorkspace, AirbyteWorkspace],
    rest_api_url: str,
    config_api_url: str,
) -> None:
    client = resource.get_client()

    test_job_endpoint = f"jobs/{TEST_JOB_ID}"
    test_job_api_url = f"{rest_api_url}/{test_job_endpoint}"

    # Create mock responses to mock full sync and poll behavior to test statuses, used only in this test
    base_api_mocks.add(
        method=responses.POST,
        url=f"{rest_api_url}/jobs",
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
        url=f"{config_api_url}/connections/get",
        json=SAMPLE_CONNECTION_DETAILS,
        status=200,
    )

    with optional_pytest_raise(
        error_expected=error_expected, exception_cls=Failure, exception_message=exception_message
    ):
        result = client.sync_and_poll(
            connection_id=TEST_CONNECTION_ID, poll_interval=0, cancel_on_termination=False
        )

    if not error_expected:
        assert result == AirbyteOutput(
            job_details=get_job_details_sample(AirbyteJobStatusType.SUCCEEDED),
            connection_details=SAMPLE_CONNECTION_DETAILS,
        )


@pytest.mark.parametrize(
    "n_polls, error_expected",
    [
        (0, False),
        (0, True),
        (4, False),
        (4, True),
        (30, False),
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
    n_polls: int,
    error_expected: bool,
    base_api_mocks: responses.RequestsMock,
    resource: Union[AirbyteCloudWorkspace, AirbyteWorkspace],
    rest_api_url: str,
    config_api_url: str,
):
    client = resource.get_client()

    # Create mock responses to mock full sync and poll behavior, used only in this test
    def _mock_interaction():
        # initial state
        base_api_mocks.add(
            method=responses.POST,
            url=f"{rest_api_url}/jobs",
            json=get_job_details_sample(status=AirbyteJobStatusType.PENDING),
            status=200,
        )
        base_api_mocks.add(
            method=responses.POST,
            url=f"{config_api_url}/connections/get",
            json=SAMPLE_CONNECTION_DETAILS,
            status=200,
        )
        # n polls before updating
        for _ in range(n_polls):
            base_api_mocks.add(
                method=responses.GET,
                url=f"{rest_api_url}/jobs/{TEST_JOB_ID}",
                json=get_job_details_sample(status=AirbyteJobStatusType.RUNNING),
                status=200,
            )
        # final state will be updated
        base_api_mocks.add(
            method=responses.GET,
            url=f"{rest_api_url}/jobs/{TEST_JOB_ID}",
            json=get_job_details_sample(
                status=AirbyteJobStatusType.SUCCEEDED
                if not error_expected
                else AirbyteJobStatusType.FAILED
            ),
            status=200,
        )
        return client.sync_and_poll(connection_id=TEST_CONNECTION_ID, poll_interval=0.1)

    with optional_pytest_raise(
        error_expected=error_expected, exception_cls=Failure, exception_message="Job failed"
    ):
        result = _mock_interaction()

    if not error_expected:
        assert result == AirbyteOutput(
            job_details=get_job_details_sample(AirbyteJobStatusType.SUCCEEDED),
            connection_details=SAMPLE_CONNECTION_DETAILS,
        )


@pytest.mark.parametrize(
    "cancel_on_termination, last_call_method",
    [
        (True, responses.DELETE),
        (False, responses.GET),
    ],
    ids=[
        "cancel_on_termination_true",
        "cancel_on_termination_false",
    ],
)
def test_airbyte_sync_and_poll_client_cancel_on_termination(
    cancel_on_termination: bool,
    last_call_method: str,
    base_api_mocks: responses.RequestsMock,
    resource: Union[AirbyteCloudWorkspace, AirbyteWorkspace],
    rest_api_url: str,
    config_api_url: str,
) -> None:
    client = resource.get_client()

    test_job_endpoint = f"jobs/{TEST_JOB_ID}"
    test_job_api_url = f"{rest_api_url}/{test_job_endpoint}"

    # Create mock responses to mock full sync and poll behavior to test statuses, used only in this test
    base_api_mocks.add(
        method=responses.POST,
        url=f"{rest_api_url}/jobs",
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
        url=f"{config_api_url}/connections/get",
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

    assert_api_call(
        base_url=rest_api_url,
        call=base_api_mocks.calls[-1],
        endpoint=test_job_endpoint,
        method=last_call_method,
    )


def test_fivetran_airbyte_cloud_sync_and_poll_materialization_method(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
    airbyte_cloud_sync_and_poll: MagicMock,
    resource: Union[AirbyteCloudWorkspace, AirbyteWorkspace],
    capsys: pytest.CaptureFixture,
) -> None:
    cleaned_connection_id = clean_name(TEST_CONNECTION_ID)

    @airbyte_assets(
        connection_id=TEST_CONNECTION_ID, workspace=resource, name=cleaned_connection_id
    )
    def my_airbyte_assets(context: AssetExecutionContext, airbyte: AirbyteCloudWorkspace):
        yield from airbyte.sync_and_poll(context=context)

    # Mocked AirbyteCloudClient.sync_and_poll returns API response where all connection tables are expected
    result = materialize(
        [my_airbyte_assets],
        resources={"airbyte": resource},
    )
    assert result.success
    asset_materializations = [
        event
        for event in result.events_for_node(cleaned_connection_id)
        if event.event_type_value == DagsterEventType.ASSET_MATERIALIZATION
    ]
    assert len(asset_materializations) == 2
    materialized_asset_keys = {
        asset_materialization.asset_key for asset_materialization in asset_materializations
    }
    assert len(materialized_asset_keys) == 2
    assert my_airbyte_assets.keys == materialized_asset_keys

    # Mocked FivetranClient.sync_and_poll returns API response
    # where one expected table is missing and an unexpected table is present
    result = materialize(
        [my_airbyte_assets],
        resources={"airbyte": resource},
    )

    assert result.success
    asset_materializations = [
        event
        for event in result.events_for_node(cleaned_connection_id)
        if event.event_type_value == DagsterEventType.ASSET_MATERIALIZATION
    ]
    assert len(asset_materializations) == 2
    materialized_asset_keys = {
        asset_materialization.asset_key for asset_materialization in asset_materializations
    }
    assert len(materialized_asset_keys) == 2
    assert my_airbyte_assets.keys != materialized_asset_keys
    assert (
        AssetKey([f"{TEST_STREAM_PREFIX}{TEST_UNEXPECTED_STREAM_NAME}"]) in materialized_asset_keys
    )
    assert (
        AssetKey([f"{TEST_STREAM_PREFIX}{TEST_ANOTHER_STREAM_NAME}"]) not in materialized_asset_keys
    )

    captured = capsys.readouterr()
    assert re.search(
        r"dagster - WARNING - (?s:.)+ - An unexpected asset was materialized", captured.err
    )
    assert re.search(r"dagster - WARNING - (?s:.)+ - Assets were not materialized", captured.err)


def test_airbyte_oss_api_url_configuration() -> None:
    """Tests that Airbyte OSS instances can configure custom API URLs."""
    with responses.RequestsMock() as response:
        resource = AirbyteWorkspace(
            rest_api_base_url=AIRBYTE_OSS_REST_API_BASE_URL,
            configuration_api_base_url=AIRBYTE_OSS_CONFIGURATION_API_BASE_URL,
            workspace_id=TEST_WORKSPACE_ID,
            username=TEST_USERNAME,
            password=TEST_PASSWORD,
        )
        client = resource.get_client()

        # Mock the API endpoints with custom URLs
        response.add(
            method=responses.GET,
            url=f"{AIRBYTE_OSS_REST_API_BASE_URL}/connections",
            json={"connections": []},
            status=200,
        )

        response.add(
            method=responses.POST,
            url=f"{AIRBYTE_OSS_CONFIGURATION_API_BASE_URL}/connections/get",
            json=SAMPLE_CONNECTION_DETAILS,
            status=200,
        )

        # Make requests and verify they go to the custom URLs
        client.get_connections()
        client.get_connection_details(connection_id=TEST_CONNECTION_ID)

        assert len(response.calls) == 2

        # Verify the calls went to the custom URLs
        assert_api_call(
            call=response.calls[0],
            base_url=AIRBYTE_OSS_REST_API_BASE_URL,
            endpoint="connections",
            method="GET",
            auth_method=AuthMethod.BASIC,
        )
        assert_api_call(
            call=response.calls[1],
            base_url=AIRBYTE_OSS_CONFIGURATION_API_BASE_URL,
            endpoint="connections/get",
            method="POST",
            object_id=TEST_CONNECTION_ID,
            auth_method=AuthMethod.BASIC,
        )


def test_airbyte_oss_username_password_auth() -> None:
    """Tests that Airbyte OSS instances can use username/password authentication."""
    with responses.RequestsMock() as response:
        resource = AirbyteWorkspace(
            rest_api_base_url=AIRBYTE_OSS_REST_API_BASE_URL,
            configuration_api_base_url=AIRBYTE_OSS_CONFIGURATION_API_BASE_URL,
            workspace_id=TEST_WORKSPACE_ID,
            username=TEST_USERNAME,
            password=TEST_PASSWORD,
        )
        client = resource.get_client()

        # Mock an API call to verify auth is working
        response.add(
            method=responses.GET,
            url=f"{AIRBYTE_OSS_REST_API_BASE_URL}/connections",
            json={"connections": []},
            status=200,
        )

        # Make a request - this should use basic auth, not bearer token
        client.get_connections()

        # Verify no token endpoint was called (basic auth doesn't need tokens)
        assert len(response.calls) == 1
        assert "/applications/token" not in response.calls[0].request.url
        #
        # # Verify auth header doesn't have Bearer token
        # auth_header = base_oss_api_mocks.calls[0].request.headers.get("Authorization", "")
        # assert not auth_header.startswith("Bearer")
        assert_api_call(
            call=response.calls[0],
            base_url=AIRBYTE_OSS_REST_API_BASE_URL,
            endpoint="connections",
            method="GET",
            auth_method=AuthMethod.BASIC,
        )


def test_airbyte_oss_client_credentials_auth() -> None:
    """Tests that Airbyte OSS instances can use client_id/client_secret authentication."""
    with responses.RequestsMock() as response:
        response.add(
            method=responses.POST,
            url=f"{AIRBYTE_OSS_REST_API_BASE_URL}/applications/token",
            json=SAMPLE_ACCESS_TOKEN,
            status=201,
        )
        resource = AirbyteWorkspace(
            rest_api_base_url=AIRBYTE_OSS_REST_API_BASE_URL,
            configuration_api_base_url=AIRBYTE_OSS_CONFIGURATION_API_BASE_URL,
            workspace_id=TEST_WORKSPACE_ID,
            client_id=TEST_CLIENT_ID,
            client_secret=TEST_CLIENT_SECRET,
        )
        client = resource.get_client()

        # Mock a test endpoint
        response.add(
            method=responses.GET,
            url=f"{AIRBYTE_OSS_REST_API_BASE_URL}/connections",
            json={"connections": []},
            status=200,
        )

        # Make a request to trigger token acquisition
        client.get_connections()

        assert len(response.calls) == 2

        # Verify token request
        assert_api_call(
            call=response.calls[1],
            base_url=AIRBYTE_OSS_REST_API_BASE_URL,
            endpoint="connections",
            method="GET",
            auth_method=AuthMethod.BEARER,
        )


def test_airbyte_oss_auth_method_mutual_exclusivity() -> None:
    """Tests that auth methods are mutually exclusive for OSS instances."""
    # Test providing both username/password and client credentials fails
    with pytest.raises(
        Exception, match="cannot provide both client_id/client_secret and username/password"
    ):
        workspace = AirbyteWorkspace(
            rest_api_base_url=AIRBYTE_OSS_REST_API_BASE_URL,
            configuration_api_base_url=AIRBYTE_OSS_CONFIGURATION_API_BASE_URL,
            workspace_id=TEST_WORKSPACE_ID,
            username=TEST_USERNAME,
            password=TEST_PASSWORD,
            client_id="test_client",
            client_secret="test_secret",
        )
        workspace.get_client()

    # Test providing incomplete username/password fails
    with pytest.raises(Exception, match="both username and password are required"):
        workspace = AirbyteWorkspace(
            rest_api_base_url=AIRBYTE_OSS_REST_API_BASE_URL,
            configuration_api_base_url=AIRBYTE_OSS_CONFIGURATION_API_BASE_URL,
            workspace_id=TEST_WORKSPACE_ID,
            username=TEST_USERNAME,
            # Missing password
        )
        workspace.get_client()

    # Test providing incomplete client credentials fails
    with pytest.raises(Exception, match="both client_id and client_secret are required"):
        workspace = AirbyteWorkspace(
            rest_api_base_url=AIRBYTE_OSS_REST_API_BASE_URL,
            configuration_api_base_url=AIRBYTE_OSS_CONFIGURATION_API_BASE_URL,
            workspace_id=TEST_WORKSPACE_ID,
            client_secret="test_secret",
            # Missing client_id
        )
        workspace.get_client()
