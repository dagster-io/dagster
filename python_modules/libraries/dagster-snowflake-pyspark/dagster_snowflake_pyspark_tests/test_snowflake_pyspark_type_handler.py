import logging
import os
import uuid
from contextlib import contextmanager
from typing import Iterator
from unittest.mock import patch

import pytest
from dagster import (
    IOManagerDefinition,
    MetadataValue,
    Out,
    TableColumn,
    TableSchema,
    build_input_context,
    build_output_context,
    job,
    op,
)
from dagster._core.storage.db_io_manager import TableSlice
from dagster_pyspark import pyspark_resource
from dagster_snowflake import build_snowflake_io_manager
from dagster_snowflake.resources import SnowflakeConnection
from dagster_snowflake_pyspark import SnowflakePySparkTypeHandler, snowflake_pyspark_io_manager
from pyspark.sql import DataFrame, SparkSession

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
def temporary_snowflake_table(schema_name: str, db_name: str, column_str: str) -> Iterator[str]:
    snowflake_config = dict(database=db_name, **SHARED_BUILDKITE_SNOWFLAKE_CONF)
    table_name = "test_io_manager_" + str(uuid.uuid4()).replace("-", "_")
    with SnowflakeConnection(
        snowflake_config, logging.getLogger("temporary_snowflake_table")
    ).get_connection() as conn:
        conn.cursor().execute(f"create table {schema_name}.{table_name} ({column_str})")
        try:
            yield table_name
        finally:
            conn.cursor().execute(f"drop table {schema_name}.{table_name}")


def test_handle_output():
    with patch("pyspark.sql.DataFrame.write") as mock_write:
        handler = SnowflakePySparkTypeHandler()

        spark = SparkSession.builder.getOrCreate()
        columns = ["col1", "col2"]
        data = [("a", "b")]
        df = spark.createDataFrame(data).toDF(*columns)

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
                TableSchema(columns=[TableColumn("col1", "string"), TableColumn("col2", "string")])
            ),
            "row_count": 1,
        }

        assert len(mock_write.method_calls) == 1


def test_load_input():
    with patch("pyspark.sql.DataFrameReader.load") as mock_read:
        spark = SparkSession.builder.getOrCreate()
        columns = ["col1", "col2"]
        data = [("a", "b")]
        df = spark.createDataFrame(data).toDF(*columns)
        mock_read.return_value = df

        handler = SnowflakePySparkTypeHandler()
        input_context = build_input_context(resource_config=resource_config)
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
        assert mock_read.called


def test_build_snowflake_pyspark_io_manager():
    assert isinstance(
        build_snowflake_io_manager([SnowflakePySparkTypeHandler()]), IOManagerDefinition
    )
    # test wrapping decorator to make sure that works as expected
    assert isinstance(snowflake_pyspark_io_manager, IOManagerDefinition)


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE snowflake DB")
def test_io_manager_with_snowflake_pyspark():
    with temporary_snowflake_table(
        schema_name="SNOWFLAKE_IO_MANAGER_SCHEMA",
        db_name="TEST_SNOWFLAKE_IO_MANAGER",
        column_str="foo string, quux integer",
    ) as table_name:
        # Create a job with the temporary table name as an output, so that it will write to that table
        # and not interfere with other runs of this test

        @op(
            out={
                table_name: Out(
                    io_manager_key="snowflake", metadata={"schema": "SNOWFLAKE_IO_MANAGER_SCHEMA"}
                )
            },
            required_resource_keys={"pyspark"},
        )
        def emit_pyspark_df(_):
            spark = SparkSession.builder.getOrCreate()
            columns = ["foo", "quux"]
            data = [("bar", 1), ("baz", 2)]
            df = spark.createDataFrame(data).toDF(*columns)
            return df

        @op(required_resource_keys={"pyspark"})
        def read_pyspark_df(df: DataFrame):
            assert set(df.schema.fields) == {"foo", "quux"}
            assert df.count() == 2

        @job(
            resource_defs={"snowflake": snowflake_pyspark_io_manager, "pyspark": pyspark_resource},
            config={
                "resources": {
                    "snowflake": {
                        "config": {
                            **SHARED_BUILDKITE_SNOWFLAKE_CONF,
                            "database": "TEST_SNOWFLAKE_IO_MANAGER",
                        }
                    },
                    "pyspark": {
                        "config": {
                            "spark_conf": {
                                "spark.jars.packages": ",".join(
                                    [
                                        "net.snowflake:snowflake-jdbc:3.8.0",
                                        "net.snowflake:spark-snowflake_2.12:2.8.2-spark_3.0",
                                    ]
                                ),
                            }
                        }
                    },
                }
            },
        )
        def io_manager_test_pipeline():
            read_pyspark_df(emit_pyspark_df())

        res = io_manager_test_pipeline.execute_in_process()
        assert res.success
