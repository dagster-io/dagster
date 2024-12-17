import responses
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.metadata.metadata_set import TableMetadataSet
from dagster._core.definitions.tags import has_kind
from dagster_airbyte import AirbyteCloudWorkspace, DagsterAirbyteTranslator
from dagster_airbyte.translator import AirbyteConnectionTableProps, AirbyteMetadataSet
from dagster_airbyte.utils import generate_table_schema

from dagster_airbyte_tests.experimental.conftest import (
    TEST_AIRBYTE_CONNECTION_TABLE_PROPS,
    TEST_CLIENT_ID,
    TEST_CLIENT_SECRET,
    TEST_CONNECTION_ID,
    TEST_CONNECTION_NAME,
    TEST_DESTINATION_DATABASE,
    TEST_DESTINATION_SCHEMA,
    TEST_DESTINATION_TYPE,
    TEST_JSON_SCHEMA,
    TEST_STREAM_NAME,
    TEST_STREAM_PREFIX,
    TEST_WORKSPACE_ID,
)


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
    assert first_table_props == TEST_AIRBYTE_CONNECTION_TABLE_PROPS


def test_translator_asset_spec(
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

    translator = DagsterAirbyteTranslator()
    asset_spec = translator.get_asset_spec(first_table_props)

    assert asset_spec.key.path == ["test_prefix_test_stream"]
    assert AirbyteMetadataSet.extract(asset_spec.metadata).connection_id == TEST_CONNECTION_ID
    assert AirbyteMetadataSet.extract(asset_spec.metadata).connection_name == TEST_CONNECTION_NAME
    assert AirbyteMetadataSet.extract(asset_spec.metadata).stream_prefix == TEST_STREAM_PREFIX
    assert (
        TableMetadataSet.extract(asset_spec.metadata).table_name
        == f"{TEST_DESTINATION_DATABASE}.{TEST_DESTINATION_SCHEMA}.{TEST_STREAM_NAME}"
    )
    assert TableMetadataSet.extract(asset_spec.metadata).column_schema == generate_table_schema(
        TEST_JSON_SCHEMA.get("properties", {})
    )
    assert has_kind(asset_spec.tags, "airbyte")
    deps = list(asset_spec.deps)
    assert len(deps) == 0


class MyCustomTranslator(DagsterAirbyteTranslator):
    def get_asset_spec(self, props: AirbyteConnectionTableProps) -> AssetSpec:
        default_spec = super().get_asset_spec(props)
        return default_spec.replace_attributes(
            key=default_spec.key.with_prefix("test_connection"),
        ).merge_attributes(metadata={"custom": "metadata"})


def test_custom_translator(
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

    translator = MyCustomTranslator()
    asset_spec = translator.get_asset_spec(first_table_props)

    assert "custom" in asset_spec.metadata
    assert asset_spec.metadata["custom"] == "metadata"
    assert asset_spec.key.path == ["test_connection", "test_prefix_test_stream"]
    assert has_kind(asset_spec.tags, "airbyte")
    assert has_kind(asset_spec.tags, TEST_DESTINATION_TYPE)
