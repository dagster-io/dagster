context = ...

# start_table_column_lineage
# Within the Dagster pipes subprocess:
lineage = {
    "a": [{"asset_key": "upstream", "column": "column1"}],
    "b": [{"asset_key": "upstream", "column": "column2"}],
}
# Then, when reporting the asset materialization:
context.report_asset_materialization(
    asset_key="foo",
    metadata={
        "lineage_meta": {
            "type": "table_column_lineage",
            "raw_value": {"table_column_lineage": lineage},
        }
    },
)
# end_table_column_lineage
