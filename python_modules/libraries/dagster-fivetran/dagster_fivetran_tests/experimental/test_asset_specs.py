import responses
from dagster._config.field_utils import EnvVar
from dagster._core.test_utils import environ
from dagster_fivetran import FivetranWorkspace, load_fivetran_asset_specs
from dagster_fivetran.asset_defs import build_fivetran_assets_definitions
from dagster_fivetran.translator import FivetranMetadataSet

from dagster_fivetran_tests.experimental.conftest import (
    TEST_ACCOUNT_ID,
    TEST_ANOTHER_ACCOUNT_ID,
    TEST_API_KEY,
    TEST_API_SECRET,
)


def test_fetch_fivetran_workspace_data(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    resource = FivetranWorkspace(
        account_id=TEST_ACCOUNT_ID, api_key=TEST_API_KEY, api_secret=TEST_API_SECRET
    )

    actual_workspace_data = resource.fetch_fivetran_workspace_data()
    assert len(actual_workspace_data.connectors_by_id) == 1
    assert len(actual_workspace_data.destinations_by_id) == 1


def test_translator_spec(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with environ({"FIVETRAN_API_KEY": TEST_API_KEY, "FIVETRAN_API_SECRET": TEST_API_SECRET}):
        resource = FivetranWorkspace(
            account_id=TEST_ACCOUNT_ID,
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        all_assets = load_fivetran_asset_specs(resource)
        all_assets_keys = [asset.key for asset in all_assets]

        # 4 tables for the connector
        assert len(all_assets) == 4
        assert len(all_assets_keys) == 4

        # Sanity check outputs, translator tests cover details here
        first_asset_key = next(key for key in all_assets_keys)
        assert first_asset_key.path == [
            "schema_name_in_destination_1",
            "table_name_in_destination_1",
        ]

        first_asset_metadata = next(asset.metadata for asset in all_assets)
        assert FivetranMetadataSet.extract(first_asset_metadata).connector_id == "connector_id"

        # clear the asset specs cache post test
        load_fivetran_asset_specs.cache_clear()


def test_cached_load_spec_single_resource(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with environ({"FIVETRAN_API_KEY": TEST_API_KEY, "FIVETRAN_API_SECRET": TEST_API_SECRET}):
        resource = FivetranWorkspace(
            account_id=TEST_ACCOUNT_ID,
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        # load asset specs a first time
        load_fivetran_asset_specs(resource)
        assert len(fetch_workspace_data_api_mocks.calls) == 4

        # load asset specs a first time, no additional calls are made
        load_fivetran_asset_specs(resource)
        assert len(fetch_workspace_data_api_mocks.calls) == 4

        # clear the asset specs cache post test
        load_fivetran_asset_specs.cache_clear()


def test_cached_load_spec_multiple_resources(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with environ({"FIVETRAN_API_KEY": TEST_API_KEY, "FIVETRAN_API_SECRET": TEST_API_SECRET}):
        resource = FivetranWorkspace(
            account_id=TEST_ACCOUNT_ID,
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        another_resource = FivetranWorkspace(
            account_id=TEST_ANOTHER_ACCOUNT_ID,
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        # load asset specs with a resource
        load_fivetran_asset_specs(resource)
        assert len(fetch_workspace_data_api_mocks.calls) == 4

        # load asset specs with another resource,
        # additional calls are made to load its specs
        load_fivetran_asset_specs(another_resource)
        assert len(fetch_workspace_data_api_mocks.calls) == 4 + 4

        # clear the asset specs cache post test
        load_fivetran_asset_specs.cache_clear()


def test_cached_load_spec_with_asset_factory(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with environ({"FIVETRAN_API_KEY": TEST_API_KEY, "FIVETRAN_API_SECRET": TEST_API_SECRET}):
        resource = FivetranWorkspace(
            account_id=TEST_ACCOUNT_ID,
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        # build_fivetran_assets_definitions calls load_fivetran_asset_specs to get the connector IDs,
        # then load_fivetran_asset_specs is called once per connector ID in fivetran_assets
        build_fivetran_assets_definitions(workspace=resource)
        assert len(fetch_workspace_data_api_mocks.calls) == 4

        # clear the asset specs cache post test
        load_fivetran_asset_specs.cache_clear()
