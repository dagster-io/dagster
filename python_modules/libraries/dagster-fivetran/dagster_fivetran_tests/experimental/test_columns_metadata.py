import re
from unittest.mock import MagicMock

import pytest
import responses
from dagster import AssetExecutionContext, AssetKey, TableColumn, TableSchema
from dagster._config.field_utils import EnvVar
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.metadata import TableMetadataSet
from dagster._core.definitions.metadata.table import TableColumnConstraints, TableConstraints
from dagster._core.test_utils import environ
from dagster_fivetran import FivetranWorkspace, fivetran_assets

from dagster_fivetran_tests.experimental.conftest import (
    SAMPLE_SOURCE_TABLE_COLUMNS_CONFIG,
    TEST_ACCOUNT_ID,
    TEST_API_KEY,
    TEST_API_SECRET,
    TEST_SCHEMA_NAME,
    TEST_SECOND_SCHEMA_NAME,
    TEST_SECOND_TABLE_NAME,
    TEST_TABLE_NAME,
    get_fivetran_connector_api_url,
)


def test_column_schema(
    connector_id: str,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
    sync_and_poll: MagicMock,
    capsys: pytest.CaptureFixture,
) -> None:
    with environ({"FIVETRAN_API_KEY": TEST_API_KEY, "FIVETRAN_API_SECRET": TEST_API_SECRET}):
        test_connector_api_url = get_fivetran_connector_api_url(connector_id)
        for schema_name, table_name in [
            (TEST_SCHEMA_NAME, TEST_TABLE_NAME),
            (TEST_SCHEMA_NAME, TEST_SECOND_TABLE_NAME),
            (TEST_SECOND_SCHEMA_NAME, TEST_TABLE_NAME),
            (TEST_SECOND_SCHEMA_NAME, TEST_SECOND_TABLE_NAME),
        ]:
            fetch_workspace_data_api_mocks.add(
                method=responses.GET,
                url=f"{test_connector_api_url}/schemas/{schema_name}/tables/{table_name}/columns",
                json=SAMPLE_SOURCE_TABLE_COLUMNS_CONFIG,
                status=200,
            )

        workspace = FivetranWorkspace(
            account_id=TEST_ACCOUNT_ID,
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        @fivetran_assets(connector_id=connector_id, workspace=workspace, name=connector_id)
        def my_fivetran_assets(context: AssetExecutionContext, fivetran: FivetranWorkspace):
            yield from fivetran.sync_and_poll(context=context).fetch_column_metadata()

        for schema_name, table_name in [
            (TEST_SCHEMA_NAME, TEST_TABLE_NAME),
            (TEST_SCHEMA_NAME, TEST_SECOND_TABLE_NAME),
            (TEST_SECOND_SCHEMA_NAME, TEST_TABLE_NAME),
            (TEST_SECOND_SCHEMA_NAME, TEST_SECOND_TABLE_NAME),
        ]:
            table_spec = my_fivetran_assets.get_asset_spec(
                AssetKey(
                    [
                        schema_name,
                        table_name,
                    ]
                )
            )
            spec_table_schema = TableMetadataSet.extract(table_spec.metadata).column_schema

            expected_spec_table_schema = TableSchema(
                columns=[
                    TableColumn(
                        name="column_name_in_destination_1",
                        type="",
                        description=None,
                        constraints=TableColumnConstraints(nullable=True, unique=False, other=[]),
                        tags={},
                    ),
                    TableColumn(
                        name="column_name_in_destination_2",
                        type="",
                        description=None,
                        constraints=TableColumnConstraints(nullable=True, unique=False, other=[]),
                        tags={},
                    ),
                ],
                constraints=TableConstraints(other=[]),
            )

            assert spec_table_schema == expected_spec_table_schema

        result = materialize(
            [my_fivetran_assets],
            resources={"fivetran": workspace},
        )
        assert result.success

        for schema_name, table_name in [
            (TEST_SCHEMA_NAME, TEST_TABLE_NAME),
            (TEST_SCHEMA_NAME, TEST_SECOND_TABLE_NAME),
            (TEST_SECOND_SCHEMA_NAME, TEST_TABLE_NAME),
            (TEST_SECOND_SCHEMA_NAME, TEST_SECOND_TABLE_NAME),
        ]:
            table_schema_by_asset_key = {
                event.materialization.asset_key: TableMetadataSet.extract(
                    event.materialization.metadata
                ).column_schema
                for event in result.get_asset_materialization_events()
                if event.materialization.asset_key
                == AssetKey(
                    [
                        schema_name,
                        table_name,
                    ]
                )
            }
            expected_table_schema_by_asset_key = {
                AssetKey(
                    [
                        schema_name,
                        table_name,
                    ]
                ): TableSchema(
                    columns=[
                        TableColumn("column_name_in_destination_1", type=""),
                        TableColumn("column_name_in_destination_2", type=""),
                    ]
                ),
            }

            assert table_schema_by_asset_key == expected_table_schema_by_asset_key

        captured = capsys.readouterr()
        # If an exception occurs in fetch_column_metadata,
        # a message is logged as a warning and the exception is not raised.
        # We test that this message is not in the logs.
        assert not re.search(
            r"dagster - WARNING - (?s:.)+ - An error occurred while fetching column metadata for table",
            captured.err,
        )
