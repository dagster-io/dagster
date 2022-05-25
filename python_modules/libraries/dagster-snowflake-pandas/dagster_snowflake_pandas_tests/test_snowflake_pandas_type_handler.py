import os
from unittest.mock import patch

import pandas
import pytest
from dagster_snowflake import build_snowflake_io_manager
from dagster_snowflake.snowflake_io_manager import TableSlice
from dagster_snowflake_pandas import SnowflakePandasTypeHandler
from pandas import DataFrame

from dagster import (
    MetadataValue,
    Out,
    TableColumn,
    TableSchema,
    build_input_context,
    build_output_context,
    job,
    op,
)

resource_config = {
    "database": "database_abc",
    "account": "account_abc",
    "user": "user_abc",
    "password": "password_abc",
    "warehouse": "warehouse_abc",
}

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


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


@op(out=Out(io_manager_key="snowflake", metadata={"schema": "snowflake_io_manager_schema"}))
def emit_pandas_df(_):
    return pandas.DataFrame({"foo": ["bar", "baz"], "quux": [1, 2]})


@op
def read_pandas_df(df: pandas.DataFrame):
    assert set(df.columns) == {"foo", "quux"}
    assert len(df.index) == 2


snowflake_io_manager = build_snowflake_io_manager([SnowflakePandasTypeHandler()])


@job(
    resource_defs={"snowflake": snowflake_io_manager},
    config={
        "resources": {
            "snowflake": {
                "config": {
                    "account": {"env": "SNOWFLAKE_ACCOUNT"},
                    "user": "BUILDKITE",
                    "password": {
                        "env": "SNOWFLAKE_BUILDKITE_PASSWORD",
                    },
                    "database": "TEST_SNOWFLAKE_IO_MANAGER",
                }
            }
        }
    },
)
def io_manager_test_pipeline():
    read_pandas_df(emit_pandas_df())


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE snowflake DB")
def test_io_manager_with_snowflake_pandas():
    res = io_manager_test_pipeline.execute_in_process()
    assert res.success
