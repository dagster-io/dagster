from typing import Callable, Union

import pytest
import responses
from dagster import AssetSpec
from dagster._core.definitions.tags import has_kind
from dagster._core.errors import DagsterInvariantViolationError
from dagster_airbyte import (
    AirbyteCloudWorkspace,
    airbyte_assets,
    build_airbyte_assets_definitions,
    load_airbyte_asset_specs,
    load_airbyte_cloud_asset_specs,
)
from dagster_airbyte.resources import AirbyteWorkspace
from dagster_airbyte.translator import (
    AirbyteConnectionTableProps,
    AirbyteMetadataSet,
    DagsterAirbyteTranslator,
)

from dagster_airbyte_tests.beta.conftest import (
    SAMPLE_ANOTHER_WORKSPACE_RESPOMSE,
    TEST_ANOTHER_WORKSPACE_ID,
    TEST_CONNECTION_ID,
    TEST_DESTINATION_TYPE,
    get_sample_connections,
    get_sample_connections_next_page,
)


def test_fetch_airbyte_workspace_data(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
    resource: Union[AirbyteCloudWorkspace, AirbyteWorkspace],
) -> None:
    actual_workspace_data = resource.fetch_airbyte_workspace_data()
    assert len(actual_workspace_data.connections_by_id) == 1
    assert len(actual_workspace_data.destinations_by_id) == 1


@pytest.mark.parametrize(
    "asset_specs_loader_fn",
    [
        (load_airbyte_asset_specs),
        (load_airbyte_cloud_asset_specs),
    ],
    ids=[
        "load_airbyte_asset_specs",
        "load_airbyte_cloud_asset_specs",
    ],
)
def test_translator_spec(
    asset_specs_loader_fn: Callable,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
    resource: Union[AirbyteCloudWorkspace, AirbyteWorkspace],
) -> None:
    all_assets = asset_specs_loader_fn(resource)
    all_assets_keys = [asset.key for asset in all_assets]

    # 1 table for the connection
    assert len(all_assets) == 2
    assert len(all_assets_keys) == 2

    # Test the asset key for the connection table
    the_asset_key = next(iter(all_assets_keys))
    assert the_asset_key.path == ["test_prefix_test_stream"]

    first_asset_metadata = next(asset.metadata for asset in all_assets)
    assert AirbyteMetadataSet.extract(first_asset_metadata).connection_id == TEST_CONNECTION_ID


@pytest.mark.parametrize(
    "asset_specs_loader_fn",
    [
        (load_airbyte_asset_specs),
        (load_airbyte_cloud_asset_specs),
    ],
    ids=[
        "load_airbyte_asset_specs",
        "load_airbyte_cloud_asset_specs",
    ],
)
def test_connection_selector(
    asset_specs_loader_fn: Callable,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
    resource: Union[AirbyteCloudWorkspace, AirbyteWorkspace],
) -> None:
    # Test with no selector (should include all connections)
    all_assets = asset_specs_loader_fn(workspace=resource)
    assert len(all_assets) == 2  # Based on the mock data

    # Test with selector that matches the connection
    matching_assets = asset_specs_loader_fn(
        workspace=resource,
        connection_selector_fn=lambda connection: connection.name == "Postgres To Snowflake",
    )
    assert len(matching_assets) == 2  # Should still get all assets from the matching connection

    # Test with selector that doesn't match any connections
    no_matching_assets = asset_specs_loader_fn(
        workspace=resource,
        connection_selector_fn=lambda connection: connection.name == "non_existent_connection",
    )
    assert len(no_matching_assets) == 0  # Should get no assets


def test_cached_load_spec_single_resource(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
    resource: Union[AirbyteCloudWorkspace, AirbyteWorkspace],
) -> None:
    # load asset specs, calls are made
    resource.load_asset_specs()
    assert len(fetch_workspace_data_api_mocks.calls) == 6

    # load asset specs another time, no additional calls are made
    resource.load_asset_specs()
    assert len(fetch_workspace_data_api_mocks.calls) == 6


def test_cached_load_spec_multiple_resources(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
    rest_api_url: str,
    config_api_url: str,
    resource: Union[AirbyteCloudWorkspace, AirbyteWorkspace],
    another_resource: Union[AirbyteCloudWorkspace, AirbyteWorkspace],
) -> None:
    fetch_workspace_data_api_mocks.add(
        method=responses.GET,
        url=f"{rest_api_url}/workspaces/{TEST_ANOTHER_WORKSPACE_ID}",
        json=SAMPLE_ANOTHER_WORKSPACE_RESPOMSE,
        status=200,
    )
    fetch_workspace_data_api_mocks.add(
        method=responses.GET,
        url=f"{rest_api_url}/connections?workspaceIds={TEST_ANOTHER_WORKSPACE_ID}",
        json=get_sample_connections(),
        status=200,
        match_querystring=True,
    )
    fetch_workspace_data_api_mocks.add(
        method=responses.GET,
        url=f"{rest_api_url}/connections?workspaceIds={TEST_ANOTHER_WORKSPACE_ID}&limit=5&offset=10",
        json=get_sample_connections_next_page(),
        status=200,
        match_querystring=True,
    )

    # load asset specs with a resource
    resource.load_asset_specs()
    assert len(fetch_workspace_data_api_mocks.calls) == 6

    # load asset specs with another resource,
    # additional calls are made to load its specs
    another_resource.load_asset_specs()
    assert len(fetch_workspace_data_api_mocks.calls) == 6 + 6


def test_cached_load_spec_with_asset_factory(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
    resource: Union[AirbyteCloudWorkspace, AirbyteWorkspace],
) -> None:
    # build_airbyte_assets_definitions calls workspace.load_asset_specs to get the connection IDs,
    # then workspace.load_asset_specs is called once per connection ID in airbyte_assets,
    # but the four calls to the API are only made once.
    build_airbyte_assets_definitions(workspace=resource)
    assert len(fetch_workspace_data_api_mocks.calls) == 6


class MyCustomTranslator(DagsterAirbyteTranslator):
    def get_asset_spec(self, data: AirbyteConnectionTableProps) -> AssetSpec:  # pyright: ignore[reportIncompatibleMethodOverride]
        default_spec = super().get_asset_spec(data)
        return default_spec.replace_attributes(
            key=default_spec.key.with_prefix("test_connection"),
        ).merge_attributes(metadata={"custom": "metadata"})


def test_translator_custom_metadata(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
    resource: Union[AirbyteCloudWorkspace, AirbyteWorkspace],
) -> None:
    all_asset_specs = resource.load_asset_specs(dagster_airbyte_translator=MyCustomTranslator())
    asset_spec = next(spec for spec in all_asset_specs)

    assert "custom" in asset_spec.metadata
    assert asset_spec.metadata["custom"] == "metadata"
    assert asset_spec.key.path == ["test_connection", "test_prefix_test_stream"]
    assert has_kind(asset_spec.tags, "airbyte")
    assert has_kind(asset_spec.tags, TEST_DESTINATION_TYPE)


class MyCustomTranslatorWithGroupName(DagsterAirbyteTranslator):
    def get_asset_spec(self, data: AirbyteConnectionTableProps) -> AssetSpec:  # pyright: ignore[reportIncompatibleMethodOverride]
        default_spec = super().get_asset_spec(data)
        return default_spec.replace_attributes(group_name="my_group_name")


def test_translator_custom_group_name_with_asset_factory(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
    resource: Union[AirbyteCloudWorkspace, AirbyteWorkspace],
) -> None:
    my_airbyte_assets = build_airbyte_assets_definitions(
        workspace=resource, dagster_airbyte_translator=MyCustomTranslatorWithGroupName()
    )

    first_assets_def = next(assets_def for assets_def in my_airbyte_assets)
    first_asset_spec = next(asset_spec for asset_spec in first_assets_def.specs)
    assert first_asset_spec.group_name == "my_group_name"


def test_translator_invariant_group_name_with_asset_decorator(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
    resource: Union[AirbyteCloudWorkspace, AirbyteWorkspace],
) -> None:
    with pytest.raises(
        DagsterInvariantViolationError,
        match="Cannot set group_name parameter on airbyte_assets",
    ):

        @airbyte_assets(
            connection_id=TEST_CONNECTION_ID,
            workspace=resource,
            group_name="my_asset_decorator_group_name",
            dagster_airbyte_translator=MyCustomTranslatorWithGroupName(),
        )
        def my_airbyte_assets(): ...
