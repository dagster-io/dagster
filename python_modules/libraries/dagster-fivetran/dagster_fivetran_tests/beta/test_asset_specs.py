import pytest
import responses
from dagster._config.field_utils import EnvVar
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.test_utils import environ
from dagster_fivetran import (
    DagsterFivetranTranslator,
    FivetranConnectorTableProps,
    FivetranWorkspace,
    load_fivetran_asset_specs,
)
from dagster_fivetran.asset_defs import build_fivetran_assets_definitions
from dagster_fivetran.translator import FivetranMetadataSet

from dagster_fivetran_tests.beta.conftest import (
    TEST_ACCOUNT_ID,
    TEST_ANOTHER_ACCOUNT_ID,
    TEST_API_KEY,
    TEST_API_SECRET,
    TEST_CONNECTOR_ID,
    TEST_CONNECTOR_NAME,
    TEST_DESTINATION_SERVICE,
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


@pytest.mark.parametrize(
    "attribute, value, expected_result_before_selection, expected_result_after_selection",
    [
        (None, None, 1, 1),
        ("name", TEST_CONNECTOR_NAME, 1, 1),
        ("id", TEST_CONNECTOR_ID, 1, 1),
        ("service", TEST_DESTINATION_SERVICE, 1, 1),
        ("name", "non_matching_name", 1, 0),
        ("id", "non_matching_id", 1, 0),
        ("service", "non_matching_service", 1, 0),
    ],
    ids=[
        "no_selector_present_connector",
        "connector_name_selector_present_connector",
        "connector_id_selector_present_connector",
        "service_selector_present_connector",
        "connector_name_selector_absent_connector",
        "connector_id_selector_absent_connector",
        "service_selector_absent_connector",
    ],
)
def test_fivetran_connector_selector(
    attribute: str,
    value: str,
    expected_result_before_selection: int,
    expected_result_after_selection: int,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    resource = FivetranWorkspace(
        account_id=TEST_ACCOUNT_ID, api_key=TEST_API_KEY, api_secret=TEST_API_SECRET
    )

    connector_selector_fn = (
        (lambda connector: getattr(connector, attribute) == value) if attribute else None
    )
    workspace_data = resource.fetch_fivetran_workspace_data()
    assert len(workspace_data.connectors_by_id) == expected_result_before_selection

    workspace_data_selection = workspace_data.to_workspace_data_selection(
        connector_selector_fn=connector_selector_fn
    )
    assert len(workspace_data_selection.connectors_by_id) == expected_result_after_selection


def test_missing_schemas_fivetran_workspace_data(
    missing_schemas_fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    resource = FivetranWorkspace(
        account_id=TEST_ACCOUNT_ID, api_key=TEST_API_KEY, api_secret=TEST_API_SECRET
    )

    actual_workspace_data = resource.fetch_fivetran_workspace_data()
    # The connector is discarded because it's missing its schemas
    assert len(actual_workspace_data.connectors_by_id) == 0
    assert len(actual_workspace_data.destinations_by_id) == 1


def test_incomplete_connector_fivetran_workspace_data(
    incomplete_connector_fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    resource = FivetranWorkspace(
        account_id=TEST_ACCOUNT_ID, api_key=TEST_API_KEY, api_secret=TEST_API_SECRET
    )

    actual_workspace_data = resource.fetch_fivetran_workspace_data()
    # The connector is discarded because it's incomplete
    assert len(actual_workspace_data.connectors_by_id) == 0
    assert len(actual_workspace_data.destinations_by_id) == 1


def test_broken_connector_fivetran_workspace_data(
    broken_connector_fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    resource = FivetranWorkspace(
        account_id=TEST_ACCOUNT_ID, api_key=TEST_API_KEY, api_secret=TEST_API_SECRET
    )

    actual_workspace_data = resource.fetch_fivetran_workspace_data()
    # The connector is discarded because it's broken
    assert len(actual_workspace_data.connectors_by_id) == 0
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
        assert FivetranMetadataSet.extract(first_asset_metadata).connector_id == TEST_CONNECTOR_ID


def test_cached_load_spec_single_resource(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with environ({"FIVETRAN_API_KEY": TEST_API_KEY, "FIVETRAN_API_SECRET": TEST_API_SECRET}):
        workspace = FivetranWorkspace(
            account_id=TEST_ACCOUNT_ID,
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        # load asset specs a first time
        workspace.load_asset_specs()
        assert len(fetch_workspace_data_api_mocks.calls) == 4

        # load asset specs a first time, no additional calls are made
        workspace.load_asset_specs()
        assert len(fetch_workspace_data_api_mocks.calls) == 4


def test_cached_load_spec_multiple_resources(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with environ({"FIVETRAN_API_KEY": TEST_API_KEY, "FIVETRAN_API_SECRET": TEST_API_SECRET}):
        workspace = FivetranWorkspace(
            account_id=TEST_ACCOUNT_ID,
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        another_workspace = FivetranWorkspace(
            account_id=TEST_ANOTHER_ACCOUNT_ID,
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        # load asset specs with a resource
        workspace.load_asset_specs()
        assert len(fetch_workspace_data_api_mocks.calls) == 4

        # load asset specs with another resource,
        # additional calls are made to load its specs
        another_workspace.load_asset_specs()
        assert len(fetch_workspace_data_api_mocks.calls) == 4 + 4


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


class MyCustomTranslator(DagsterFivetranTranslator):
    def get_asset_spec(self, data: FivetranConnectorTableProps) -> AssetSpec:  # pyright: ignore[reportIncompatibleMethodOverride]
        default_spec = super().get_asset_spec(data)
        return default_spec.replace_attributes(
            key=default_spec.key.with_prefix("prefix"),
            metadata={**default_spec.metadata, "custom": "metadata"},
        )


def test_translator_custom_metadata(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with environ({"FIVETRAN_API_KEY": TEST_API_KEY, "FIVETRAN_API_SECRET": TEST_API_SECRET}):
        workspace = FivetranWorkspace(
            account_id=TEST_ACCOUNT_ID,
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        all_asset_specs = load_fivetran_asset_specs(
            workspace=workspace, dagster_fivetran_translator=MyCustomTranslator()
        )
        asset_spec = next(spec for spec in all_asset_specs)

        assert "custom" in asset_spec.metadata
        assert asset_spec.metadata["custom"] == "metadata"
        assert asset_spec.key.path == [
            "prefix",
            "schema_name_in_destination_1",
            "table_name_in_destination_1",
        ]
        assert "dagster/kind/fivetran" in asset_spec.tags


class MyAssetFactoryCustomTranslator(DagsterFivetranTranslator):
    def get_asset_spec(self, data: FivetranConnectorTableProps) -> AssetSpec:  # pyright: ignore[reportIncompatibleMethodOverride]
        default_spec = super().get_asset_spec(data)
        return default_spec.replace_attributes(group_name="my_group_name")


def test_translator_custom_group_name_with_asset_factory(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with environ({"FIVETRAN_API_KEY": TEST_API_KEY, "FIVETRAN_API_SECRET": TEST_API_SECRET}):
        resource = FivetranWorkspace(
            account_id=TEST_ACCOUNT_ID,
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        my_fivetran_assets = build_fivetran_assets_definitions(
            workspace=resource, dagster_fivetran_translator=MyAssetFactoryCustomTranslator()
        )

        first_assets_def = next(assets_def for assets_def in my_fivetran_assets)
        first_asset_spec = next(asset_spec for asset_spec in first_assets_def.specs)
        assert first_asset_spec.group_name == "my_group_name"
