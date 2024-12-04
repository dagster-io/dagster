import responses
from dagster_airbyte import AirbyteCloudWorkspace

from dagster_airbyte_tests.experimental.conftest import (
    TEST_CLIENT_ID,
    TEST_CLIENT_SECRET,
    TEST_CONNECTION_ID,
    TEST_PREFIX,
    TEST_STREAM_NAME,
    TEST_WORKSPACE_ID,
)


def test_fetch_airbyte_workspace_data(
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


def test_airbyte_workspace_data_to_table_props(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    resource = AirbyteCloudWorkspace(
        workspace_id=TEST_WORKSPACE_ID,
        client_id=TEST_CLIENT_ID,
        client_secret=TEST_CLIENT_SECRET,
    )

    table_props_data = (
        resource.fetch_airbyte_workspace_data().to_airbyte_connection_table_props_data()
    )
    assert len(table_props_data) == 1
    first_table_props = next(iter(table_props_data))
    assert first_table_props.table_name == f"{TEST_PREFIX}{TEST_STREAM_NAME}"
    assert first_table_props.connection_id == TEST_CONNECTION_ID
