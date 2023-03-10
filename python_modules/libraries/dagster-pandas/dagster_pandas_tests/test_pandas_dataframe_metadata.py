from pandas import DataFrame
from dagster import TypeCheck, MetadataValue, TableSchema, TableColumn
from dagster_pandas.data_frame import create_dagster_pandas_dataframe_metadata


def test_create_dagster_pandas_dataframe_metadata():
    # Test with a valid DataFrame
    df = DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
    expected_table_schema = TableSchema(
        columns=[TableColumn(name="col1", type="int64"), TableColumn(name="col2", type="object")]
    )
    assert create_dagster_pandas_dataframe_metadata(df) == MetadataValue.table_schema(expected_table_schema)

    # Test with an invalid input
    invalid_input = "not a DataFrame"
    assert create_dagster_pandas_dataframe_metadata(invalid_input) == TypeCheck(success=False)
