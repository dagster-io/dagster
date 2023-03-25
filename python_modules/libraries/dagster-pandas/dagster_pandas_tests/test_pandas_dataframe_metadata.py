from dagster import MetadataValue, TableColumn, TableSchema
from dagster_pandas.data_frame import create_table_schema_metadata_from_dataframe
from pandas import DataFrame


def test_create_table_schema_metadata_from_dataframe():
    # Test with a valid DataFrame
    df = DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
    expected_table_schema = TableSchema(
        columns=[TableColumn(name="col1", type="int64"), TableColumn(name="col2", type="object")]
    )
    assert create_table_schema_metadata_from_dataframe(df) == MetadataValue.table_schema(
        expected_table_schema
    )
