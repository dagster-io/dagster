from collections.abc import Set
from typing import Optional

import pytest
import responses
from dagster._config.field_utils import EnvVar
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.test_utils import environ
from dagster_fivetran import (
    DagsterFivetranTranslator,
    FivetranConnectorTableProps,
    FivetranFilter,
    FivetranWorkspace,
    load_fivetran_asset_specs,
)
from dagster_fivetran.asset_defs import build_fivetran_assets_definitions
from dagster_fivetran.translator import FivetranMetadataSet

from dagster_fivetran_tests.beta.conftest import (
    FIVETRAN_API_BASE,
    FIVETRAN_API_VERSION,
    TEST_ACCOUNT_ID,
    TEST_ANOTHER_ACCOUNT_ID,
    TEST_API_KEY,
    TEST_API_SECRET,
    TEST_CONNECTOR_ID,
    TEST_CONNECTOR_NAME,
    TEST_DESTINATION_DATABASE,
    TEST_DESTINATION_ID,
    TEST_DESTINATION_SERVICE,
    get_fivetran_connector_api_url,
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
    "connector_names, connector_ids, databases, services, expected_result, skip_connector_call, skip_schema_config_call",
    [
        (None, None, None, None, 1, False, False),
        ({TEST_CONNECTOR_NAME}, None, None, None, 1, False, False),
        (None, {TEST_CONNECTOR_ID}, None, None, 1, False, False),
        (None, None, {TEST_DESTINATION_DATABASE}, None, 1, False, False),
        (None, None, None, {TEST_DESTINATION_SERVICE}, 1, False, False),
        (
            {TEST_CONNECTOR_NAME},
            {TEST_CONNECTOR_ID},
            {TEST_DESTINATION_DATABASE},
            {TEST_DESTINATION_SERVICE},
            1,
            False,
            False,
        ),
        ({"non_matching_connector_name"}, None, None, None, 0, False, True),
        (None, {"non_matching_connector_id"}, None, None, 0, False, True),
        (None, None, {"non_matching_database"}, None, 0, True, True),
        (None, None, None, {"non_matching_service"}, 0, True, True),
        (
            {"non_matching_connector_name"},
            {"non_matching_connector_id"},
            {"non_matching_database"},
            {"non_matching_service"},
            0,
            True,
            True,
        ),
        (
            {TEST_CONNECTOR_NAME},
            {TEST_CONNECTOR_ID},
            {"non_matching_database"},
            None,
            0,
            True,
            True,
        ),
        (
            {"non_matching_connector_name"},
            None,
            {TEST_DESTINATION_DATABASE},
            {TEST_DESTINATION_SERVICE},
            0,
            False,
            True,
        ),
    ],
    ids=[
        "no_filter_present_connector",
        "connector_name_filter_present_connector",
        "connector_id_filter_present_connector",
        "database_filter_present_connector",
        "service_filter_present_connector",
        "all_filters_present_connector",
        "connector_name_filter_absent_connector",
        "connector_id_filter_absent_connector",
        "database_filter_absent_connector",
        "service_filter_absent_connector",
        "all_filters_absent_connector",
        "one_non_matching_database_filter_absent_connector",
        "one_non_matching_connector_filter_absent_connector",
    ],
)
def test_fivetran_filter(
    connector_names: Optional[Set[str]],
    connector_ids: Optional[Set[str]],
    databases: Optional[Set[str]],
    services: Optional[Set[str]],
    expected_result: int,
    skip_connector_call: bool,
    skip_schema_config_call: bool,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    resource = FivetranWorkspace(
        account_id=TEST_ACCOUNT_ID, api_key=TEST_API_KEY, api_secret=TEST_API_SECRET
    )

    # When a destination is filtered out, all its connector are filtered out
    # and calls to the `/groups/{group_id}/connectors` endpoint are skipped.
    # We remove the call from the mock calls to avoid the exception
    # raised by RequestMock when not all requests are executed.
    if skip_connector_call:
        fetch_workspace_data_api_mocks.remove(
            method_or_response=responses.GET,
            url=f"{FIVETRAN_API_BASE}/{FIVETRAN_API_VERSION}/groups/{TEST_DESTINATION_ID}/connectors",
        )
    # When a connector is filtered out, the call to the `connectors/{connector_id}/schemas` endpoint is skipped.
    # We remove the call from the mock calls to avoid the exception
    # raised by RequestMock when not all requests are executed.
    if skip_schema_config_call:
        fetch_workspace_data_api_mocks.remove(
            method_or_response=responses.GET,
            url=f"{get_fivetran_connector_api_url(TEST_CONNECTOR_ID)}/schemas",
        )

    fivetran_filter = FivetranFilter(
        connector_names=connector_names,
        connector_ids=connector_ids,
        databases=databases,
        services=services,
    )
    actual_workspace_data = resource.fetch_fivetran_workspace_data(fivetran_filter=fivetran_filter)
    assert len(actual_workspace_data.connectors_by_id) == expected_result


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
    def get_asset_spec(self, data: FivetranConnectorTableProps) -> AssetSpec:
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
