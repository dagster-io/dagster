from typing import Callable

import responses
from dagster._config.field_utils import EnvVar
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.test_utils import environ
from dagster_fivetran import (
    DagsterFivetranTranslator,
    FivetranConnectorTableProps,
    FivetranWorkspace,
)

from dagster_fivetran_tests.experimental.conftest import (
    TEST_ACCOUNT_ID,
    TEST_API_KEY,
    TEST_API_SECRET,
)


def test_fivetran_workspace_data_to_fivetran_connector_table_props_data(
    fetch_workspace_data_api_mocks: Callable,
) -> None:
    resource = FivetranWorkspace(
        account_id=TEST_ACCOUNT_ID, api_key=TEST_API_KEY, api_secret=TEST_API_SECRET
    )

    actual_workspace_data = resource.fetch_fivetran_workspace_data()
    table_props_data = actual_workspace_data.to_fivetran_connector_table_props_data()
    assert len(table_props_data) == 4
    assert table_props_data[0].table == "schema_name_in_destination_1.table_name_in_destination_1"
    assert table_props_data[1].table == "schema_name_in_destination_1.table_name_in_destination_2"
    assert table_props_data[2].table == "schema_name_in_destination_2.table_name_in_destination_1"
    assert table_props_data[3].table == "schema_name_in_destination_2.table_name_in_destination_2"


class MyCustomTranslator(DagsterFivetranTranslator):
    def get_asset_spec(self, props: FivetranConnectorTableProps) -> AssetSpec:
        default_spec = super().get_asset_spec(props)
        return default_spec.replace_attributes(
            key=default_spec.key.with_prefix("prefix"),
            metadata={**default_spec.metadata, "custom": "metadata"},
        )


def test_translator_custom_metadata(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with environ({"FIVETRAN_API_KEY": TEST_API_KEY, "FIVETRAN_API_SECRET": TEST_API_SECRET}):
        resource = FivetranWorkspace(
            account_id=TEST_ACCOUNT_ID,
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        actual_workspace_data = resource.fetch_fivetran_workspace_data()
        table_props_data = actual_workspace_data.to_fivetran_connector_table_props_data()

        first_table_props_data = next(props for props in table_props_data)

        asset_spec = MyCustomTranslator().get_asset_spec(first_table_props_data)

        assert "custom" in asset_spec.metadata
        assert asset_spec.metadata["custom"] == "metadata"
        assert asset_spec.key.path == [
            "prefix",
            "schema_name_in_destination_1",
            "table_name_in_destination_1",
        ]
        assert "dagster/kind/fivetran" in asset_spec.tags
