import logging
import os
import uuid
from contextlib import contextmanager
from typing import Iterator
from unittest.mock import patch

import pandas
import pytest
from dagster_snowflake import build_snowflake_io_manager
from dagster_snowflake.resources import SnowflakeConnection
from dagster_snowflake.snowflake_io_manager import TableSlice
from dagster_snowflake_pandas import SnowflakePandasTypeHandler
from dagster_snowflake_pandas.snowflake_pandas_type_handler import (
    _convert_string_to_timestamp,
    _convert_timestamp_to_string,
)
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


SHARED_BUILDKITE_SNOWFLAKE_CONF = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT", ""),
    "user": "BUILDKITE",
    "password": os.getenv("SNOWFLAKE_BUILDKITE_PASSWORD", ""),
}


@contextmanager
def temporary_snowflake_table(schema_name: str, db_name: str) -> Iterator[str]:
    snowflake_config = dict(database=db_name, **SHARED_BUILDKITE_SNOWFLAKE_CONF)
    table_name = "test_io_manager_" + str(uuid.uuid4()).replace("-", "_")
    with SnowflakeConnection(
        snowflake_config, logging.getLogger("temporary_snowflake_table")
    ).get_connection() as conn:
        conn.cursor().execute(f"create table {schema_name}.{table_name} (foo string, quux integer)")
        try:
            yield table_name
        finally:
            conn.cursor().execute(f"drop table {schema_name}.{table_name}")


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
        "dagster_snowflake_pandas.snowflake_pandas_type_handler.pd.read_sql"
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


def test_type_conversions():
    # no timestamp data
    no_time = pandas.Series([1, 2, 3, 4, 5])
    converted = _convert_string_to_timestamp(_convert_timestamp_to_string(no_time))

    assert (converted == no_time).all()

    # timestamp data
    with_time = pandas.Series(
        [
            pandas.Timestamp("2017-01-01T12:30:45.35"),
            pandas.Timestamp("2017-02-01T12:30:45.35"),
            pandas.Timestamp("2017-03-01T12:30:45.35"),
        ]
    )
    time_converted = _convert_string_to_timestamp(_convert_timestamp_to_string(with_time))

    assert (with_time == time_converted).all()

    # string that isn't a time
    string_data = pandas.Series(["not", "a", "timestamp"])

    assert (_convert_string_to_timestamp(string_data) == string_data).all()


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE snowflake DB")
def test_io_manager_with_snowflake_pandas():
    with temporary_snowflake_table(
        schema_name="SNOWFLAKE_IO_MANAGER_SCHEMA", db_name="TEST_SNOWFLAKE_IO_MANAGER"
    ) as table_name:

        # Create a job with the temporary table name as an output, so that it will write to that table
        # and not interfere with other runs of this test

        @op(
            out={
                table_name: Out(
                    io_manager_key="snowflake", metadata={"schema": "SNOWFLAKE_IO_MANAGER_SCHEMA"}
                )
            }
        )
        def emit_pandas_df(_):
            return pandas.DataFrame({"foo": ["bar", "baz"], "quux": [1, 2]})

        @op
        def read_pandas_df(df: pandas.DataFrame):
            assert set(df.columns) == {"foo", "quux"}
            assert len(df.index) == 2

        time_df = pandas.DataFrame(
            {
                "foo": ["bar", "baz"],
                "date": [
                    pandas.Timestamp("2017-01-01T12:30:45.35"),
                    pandas.Timestamp("2017-02-01T12:30:45.35"),
                ],
            }
        )

        @op(
            out={
                table_name: Out(
                    io_manager_key="snowflake", metadata={"schema": "SNOWFLAKE_IO_MANAGER_SCHEMA"}
                )
            }
        )
        def emit_time_df(_):
            return time_df

        @op
        def read_time_df(df: pandas.DataFrame):
            assert set(df.columns) == {"foo", "date"}
            assert (df == time_df).all()

        snowflake_io_manager = build_snowflake_io_manager([SnowflakePandasTypeHandler()])

        @job(
            resource_defs={"snowflake": snowflake_io_manager},
            config={
                "resources": {
                    "snowflake": {
                        "config": {
                            **SHARED_BUILDKITE_SNOWFLAKE_CONF,
                            "database": "TEST_SNOWFLAKE_IO_MANAGER",
                        }
                    }
                }
            },
        )
        def io_manager_test_pipeline():
            read_pandas_df(emit_pandas_df())
            read_time_df(emit_time_df())

        res = io_manager_test_pipeline.execute_in_process()
        assert res.success
