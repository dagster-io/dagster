import responses
from dagster_airbyte import AirbyteCloudWorkspace

from dagster_airbyte_tests.experimental.conftest import (
    TEST_CLIENT_ID,
    TEST_CLIENT_SECRET,
    TEST_WORKSPACE_ID,
)


def test_fetch_fivetran_workspace_data(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    resource = AirbyteCloudWorkspace(
        workspace_id=TEST_WORKSPACE_ID,
        client_id=TEST_CLIENT_ID,
        client_secret=TEST_CLIENT_SECRET,
    )

    actual_workspace_data = resource.fetch_airbyte_workspace_data()
    assert len(actual_workspace_data.connections_by_id) == 1
    assert len(actual_workspace_data.destinations_by_id) == 1
