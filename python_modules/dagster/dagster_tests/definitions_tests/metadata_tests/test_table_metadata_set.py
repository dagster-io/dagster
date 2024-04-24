import pytest
from dagster import AssetKey, AssetMaterialization, TableColumn, TableSchema
from dagster._check import CheckError
from dagster._core.definitions.metadata import TableMetadataSet
from dagster._core.definitions.metadata.table import TableColumnDep, TableColumnLineage


def test_table_metadata_set():
    column_schema = TableSchema(columns=[TableColumn("foo", "str")])
    table_metadata = TableMetadataSet(column_schema=column_schema)

    dict_table_metadata = dict(table_metadata)
    assert dict_table_metadata == {"dagster/column_schema": column_schema}
    assert isinstance(dict_table_metadata["dagster/column_schema"], TableSchema)
    AssetMaterialization(asset_key="a", metadata=dict_table_metadata)

    splat_table_metadata = {**table_metadata}
    assert splat_table_metadata == {"dagster/column_schema": column_schema}
    assert isinstance(splat_table_metadata["dagster/column_schema"], TableSchema)
    AssetMaterialization(asset_key="a", metadata=splat_table_metadata)

    assert dict(TableMetadataSet()) == {}
    assert TableMetadataSet.extract(dict(TableMetadataSet())) == TableMetadataSet()


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

    table_metadata = TableMetadataSet(
        column_lineage=TableColumnLineage(
            {
                "column": list(reversed(expected_deps)),
            }
        )
    )

    dict_table_metadata = dict(table_metadata)
    assert dict_table_metadata == expected_metadata

    materialization = AssetMaterialization(asset_key="foo", metadata=dict_table_metadata)
    extracted_table_metadata = TableMetadataSet.extract(materialization.metadata)
    assert extracted_table_metadata.column_lineage == expected_column_lineage

    splat_table_metadata = {**table_metadata}
    assert splat_table_metadata == expected_metadata

    materialization = AssetMaterialization(asset_key="foo", metadata=splat_table_metadata)
    extracted_table_metadata = TableMetadataSet.extract(materialization.metadata)
    assert extracted_table_metadata.column_lineage == expected_column_lineage
