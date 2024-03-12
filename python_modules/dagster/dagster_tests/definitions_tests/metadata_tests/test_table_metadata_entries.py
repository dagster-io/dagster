from dagster import AssetMaterialization, TableSchema
from dagster._core.definitions.metadata import TableMetadataEntries


def test_table_metadata_entries():
    assert dict(TableMetadataEntries()) == {}
    assert TableMetadataEntries.from_dict(dict(TableMetadataEntries())) == TableMetadataEntries()

    column_schema = TableSchema(columns=[])
    table_metadata_entries = TableMetadataEntries(column_schema=column_schema)
    assert dict(table_metadata_entries) == {"dagster/column_schema": column_schema}
    assert {**table_metadata_entries} == {"dagster/column_schema": column_schema}
    assert TableMetadataEntries.from_dict(dict(table_metadata_entries)) == table_metadata_entries

    AssetMaterialization(asset_key="a", metadata=dict(table_metadata_entries))
