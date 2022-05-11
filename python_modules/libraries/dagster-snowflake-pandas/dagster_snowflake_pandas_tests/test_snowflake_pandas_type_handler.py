from unittest.mock import patch

from dagster_snowflake.snowflake_io_manager import TableSlice
from dagster_snowflake_pandas import SnowflakePandasTypeHandler
from pandas import DataFrame

from dagster import (
    MetadataValue,
    TableColumn,
    TableSchema,
    build_input_context,
    build_output_context,
)

resource_config = {
    "database": "database_abc",
    "account": "account_abc",
    "user": "user_abc",
    "password": "password_abc",
    "warehouse": "warehouse_abc",
}


def test_handle_output():
    with patch("dagster_snowflake_pandas.snowflake_pandas_type_handler._connect_snowflake"):
        handler = SnowflakePandasTypeHandler()
        df = DataFrame([{"col1": "a", "col2": 1}])
        output_context = build_output_context(resource_config=resource_config)

        metadata = handler.handle_output(
            output_context,
            TableSlice(
                table="my_table",
                schema="my_schema",
                database="my_db",
                columns=None,
                partition=None,
            ),
            df,
        )

        assert metadata == {
            "dataframe_columns": MetadataValue.table_schema(
                TableSchema(columns=[TableColumn("col1", "object"), TableColumn("col2", "int64")])
            ),
            "row_count": 1,
        }


def test_load_input():
    with patch("dagster_snowflake_pandas.snowflake_pandas_type_handler._connect_snowflake"), patch(
        "dagster_snowflake_pandas.snowflake_pandas_type_handler.read_sql"
    ) as mock_read_sql:
        mock_read_sql.return_value = DataFrame([{"COL1": "a", "COL2": 1}])

        handler = SnowflakePandasTypeHandler()
        input_context = build_input_context()
        df = handler.load_input(
            input_context,
            TableSlice(
                table="my_table",
                schema="my_schema",
                database="my_db",
                columns=None,
                partition=None,
            ),
        )
        assert mock_read_sql.call_args_list[0][1]["sql"] == "SELECT * FROM my_db.my_schema.my_table"
        assert df.equals(DataFrame([{"col1": "a", "col2": 1}]))
