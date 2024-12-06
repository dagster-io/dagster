import responses
from dagster._config.field_utils import EnvVar
from dagster._core.test_utils import environ
from dagster_airbyte import AirbyteCloudWorkspace, load_airbyte_cloud_asset_specs

from dagster_airbyte_tests.experimental.conftest import (
    TEST_CLIENT_ID,
    TEST_CLIENT_SECRET,
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


def test_translator_spec(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with environ(
        {"AIRBYTE_CLIENT_ID": TEST_CLIENT_ID, "AIRBYTE_CLIENT_SECRET": TEST_CLIENT_SECRET}
    ):
        resource = AirbyteCloudWorkspace(
            workspace_id=TEST_WORKSPACE_ID,
            client_id=EnvVar("AIRBYTE_CLIENT_ID"),
            client_secret=EnvVar("AIRBYTE_CLIENT_SECRET"),
        )

        all_assets = load_airbyte_cloud_asset_specs(resource)
        all_assets_keys = [asset.key for asset in all_assets]

        # 1 table for the connection
        assert len(all_assets) == 1
        assert len(all_assets_keys) == 1

        # Test the asset key for the connection table
        the_asset_key = next(iter(all_assets_keys))
        assert the_asset_key.path == ["test_prefix_test_stream"]
