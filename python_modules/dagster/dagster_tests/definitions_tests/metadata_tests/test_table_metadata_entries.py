import pytest
from dagster import AssetKey, AssetMaterialization, TableColumn, TableSchema
from dagster._check import CheckError
from dagster._core.definitions.metadata import (
    TableMetadataEntries,
)
from dagster._core.definitions.metadata.table import (
    TableColumnDep,
    TableColumnLineage,
)


def test_table_metadata_entries():
    column_schema = TableSchema(columns=[TableColumn("foo", "str")])
    table_metadata_entries = TableMetadataEntries(column_schema=column_schema)

    dict_table_metadata_entries = dict(table_metadata_entries)
    assert dict_table_metadata_entries == {"dagster/column_schema": column_schema}
    assert isinstance(dict_table_metadata_entries["dagster/column_schema"], TableSchema)
    AssetMaterialization(asset_key="a", metadata=dict_table_metadata_entries)

    splat_table_metadata_entries = {**table_metadata_entries}
    assert splat_table_metadata_entries == {"dagster/column_schema": column_schema}
    assert isinstance(splat_table_metadata_entries["dagster/column_schema"], TableSchema)
    AssetMaterialization(asset_key="a", metadata=splat_table_metadata_entries)

    assert dict(TableMetadataEntries()) == {}
    assert TableMetadataEntries.extract(dict(TableMetadataEntries())) == TableMetadataEntries()


def test_invalid_column_lineage() -> None:
    with pytest.raises(CheckError):
        TableColumnLineage(
            {
                "column": [
                    TableColumnDep(
                        asset_key=AssetKey("upstream"),
                        column_name="upstream_column",
                    ),
                    TableColumnDep(
                        asset_key=AssetKey("upstream"),
                        column_name="upstream_column",
                    ),
                ],
            }
        )


def test_column_lineage() -> None:
    expected_deps = [
        TableColumnDep(
            asset_key=AssetKey("upstream"),
            column_name="upstream_column_b",
        ),
        TableColumnDep(
            asset_key=AssetKey("upstream"),
            column_name="upstream_column_a",
        ),
    ]
    expected_column_lineage = TableColumnLineage(
        {
            "column": expected_deps,
        }
    )
    expected_metadata = {"dagster/column_lineage": expected_column_lineage}

    table_metadata_entries = TableMetadataEntries(
        column_lineage=TableColumnLineage(
            {
                "column": list(reversed(expected_deps)),
            }
        )
    )

    dict_table_metadata_entries = dict(table_metadata_entries)
    assert dict_table_metadata_entries == expected_metadata

    materialization = AssetMaterialization(asset_key="foo", metadata=dict_table_metadata_entries)
    extracted_table_metadata_entries = TableMetadataEntries.extract(materialization.metadata)
    assert extracted_table_metadata_entries.column_lineage == expected_column_lineage

    splat_table_metadata_entries = {**table_metadata_entries}
    assert splat_table_metadata_entries == expected_metadata

    materialization = AssetMaterialization(asset_key="foo", metadata=splat_table_metadata_entries)
    extracted_table_metadata_entries = TableMetadataEntries.extract(materialization.metadata)
    assert extracted_table_metadata_entries.column_lineage == expected_column_lineage
