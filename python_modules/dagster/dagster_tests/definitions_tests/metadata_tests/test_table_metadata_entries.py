from dagster import AssetMaterialization, TableColumn, TableSchema
from dagster._core.definitions.metadata import TableMetadataEntries


def test_table_metadata_entries():
    column_schema = TableSchema(columns=[TableColumn("foo", "str")])
    table_metadata_entries = TableMetadataEntries(column_schema=column_schema)

    table_metadata_entries_dict = table_metadata_entries.dict()
    assert table_metadata_entries_dict == {"dagster/column_schema": column_schema}
    assert isinstance(table_metadata_entries_dict["dagster/column_schema"], TableSchema)
    AssetMaterialization(asset_key="a", metadata=table_metadata_entries_dict)

    dict_table_metadata_entries = dict(table_metadata_entries)
    assert dict_table_metadata_entries == {"dagster/column_schema": column_schema}
    assert isinstance(dict_table_metadata_entries["dagster/column_schema"], TableSchema)
    AssetMaterialization(asset_key="a", metadata=dict_table_metadata_entries)

    splat_table_metadata_entries = {**table_metadata_entries}
    assert splat_table_metadata_entries == {"dagster/column_schema": column_schema}
    assert isinstance(splat_table_metadata_entries["dagster/column_schema"], TableSchema)
    AssetMaterialization(asset_key="a", metadata=splat_table_metadata_entries)

    assert dict(TableMetadataEntries()) == {}
    assert TableMetadataEntries.from_dict(dict(TableMetadataEntries())) == TableMetadataEntries()
