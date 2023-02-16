import os
import uuid
from contextlib import contextmanager
from typing import Iterator
from unittest.mock import patch

import pandas_gbq
import pytest
from dagster import (
    DailyPartitionsDefinition,
    DynamicPartitionsDefinition,
    IOManagerDefinition,
    MetadataValue,
    MultiPartitionKey,
    MultiPartitionsDefinition,
    Out,
    StaticPartitionsDefinition,
    TableColumn,
    TableSchema,
    asset,
    build_input_context,
    build_output_context,
    instance_for_test,
    job,
    materialize,
    op,
)
from dagster._core.storage.db_io_manager import TableSlice
from dagster_gcp import build_bigquery_io_manager
from dagster_gcp_pyspark import BigQueryPySparkTypeHandler, bigquery_pyspark_io_manager
from google.cloud import bigquery
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, to_date
from pyspark.sql.types import LongType, StringType, StructField, StructType

resource_config = {
    "database": "database_abc",
    "account": "account_abc",
    "user": "user_abc",
    "password": "password_abc",
    "warehouse": "warehouse_abc",
}

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


SHARED_BUILDKITE_BQ_CONFIG = {
    "project": os.getenv("GCP_PROJECT_ID"),
}

BIGQUERY_JARS = "gs://spark-lib/bigquery/spark-bigquery-with-dependencies_2.12-0.23.2.jar"


@contextmanager
def temporary_bigquery_table(schema_name: str, column_str: str) -> Iterator[str]:
    bq_client = bigquery.Client(
        project=SHARED_BUILDKITE_BQ_CONFIG["project"],
    )
    table_name = "test_io_manager_" + str(uuid.uuid4()).replace("-", "_")
    bq_client.query(f"create table {schema_name}.{table_name} ({column_str})").result()
    try:
        yield table_name
    finally:
        bq_client.query(
            f"drop table {SHARED_BUILDKITE_BQ_CONFIG['project']}.{schema_name}.{table_name}"
        ).result()


def test_handle_output():
    with patch("pyspark.sql.DataFrame.write") as mock_write:
        handler = BigQueryPySparkTypeHandler()

        spark = SparkSession.builder.config(
            key="spark.jars.packages",
            value=BIGQUERY_JARS,
        ).getOrCreate()
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
                partition_dimensions=None,
            ),
            df,
        )

        assert metadata == {
            "dataframe_columns": MetadataValue.table_schema(
                TableSchema(columns=[TableColumn("col1", "string"), TableColumn("col2", "string")])
            ),
        }

        assert len(mock_write.method_calls) == 1


def test_load_input():
    with patch("pyspark.sql.DataFrameReader.load") as mock_read:
        spark = SparkSession.builder.config(
            key="spark.jars.packages",
            value=BIGQUERY_JARS,
        ).getOrCreate()
        columns = ["col1", "col2"]
        data = [("a", "b")]
        df = spark.createDataFrame(data).toDF(*columns)
        mock_read.return_value = df

        handler = BigQueryPySparkTypeHandler()
        input_context = build_input_context(resource_config=resource_config)
        df = handler.load_input(
            input_context,
            TableSlice(
                table="my_table",
                schema="my_schema",
                database="my_db",
                columns=None,
                partition_dimensions=None,
            ),
        )
        assert mock_read.called


def test_build_bigquery_pyspark_io_manager():
    assert isinstance(
        build_bigquery_io_manager([BigQueryPySparkTypeHandler()]), IOManagerDefinition
    )
    # test wrapping decorator to make sure that works as expected
    assert isinstance(bigquery_pyspark_io_manager, IOManagerDefinition)


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE snowflake DB")
def test_io_manager_with_snowflake_pyspark():
    schema = "BIGQUERY_IO_MANAGER_SCHEMA"
    with temporary_bigquery_table(
        schema_name=schema,
        column_str="foo string, quux integer",
    ) as table_name:
        # Create a job with the temporary table name as an output, so that it will write to that table
        # and not interfere with other runs of this test

        @op(
            out={table_name: Out(dagster_type=DataFrame, metadata={"schema": schema})},
        )
        def emit_pyspark_df(_):
            spark = SparkSession.builder.config(
                key="spark.jars.packages",
                value=BIGQUERY_JARS,
            ).getOrCreate()
            columns = ["foo", "quux"]
            data = [("bar", 1), ("baz", 2)]
            df = spark.createDataFrame(data).toDF(*columns)
            return df

        @op
        def read_pyspark_df(df: DataFrame) -> None:
            assert set([f.name for f in df.schema.fields]) == {"foo", "quux"}
            assert df.count() == 2

        @job(
            resource_defs={
                "io_manager": bigquery_pyspark_io_manager.configured(SHARED_BUILDKITE_BQ_CONFIG)
            }
        )
        def io_manager_test_pipeline():
            read_pyspark_df(emit_pyspark_df())

        res = io_manager_test_pipeline.execute_in_process()
        assert res.success


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE snowflake DB")
def test_time_window_partitioned_asset():
    schema = "BIGQUERY_IO_MANAGER_SCHEMA"
    with temporary_bigquery_table(
        schema_name=schema,
        column_str="foo string, quux integer",
    ) as table_name:

        @asset(
            partitions_def=DailyPartitionsDefinition(start_date="2022-01-01"),
            metadata={"partition_expr": "time"},
            config_schema={"value": str},
            key_prefix=schema,
            name=table_name,
        )
        def daily_partitioned(context) -> DataFrame:
            partition = context.asset_partition_key_for_output()
            value = context.op_config["value"]

            spark = SparkSession.builder.config(
                key="spark.jars.packages",
                value=BIGQUERY_JARS,
            ).getOrCreate()

            schema = StructType(
                [
                    StructField("RAW_TIME", StringType()),
                    StructField("A", StringType()),
                    StructField("B", LongType()),
                ]
            )
            data = [
                (partition, value, 4),
                (partition, value, 5),
                (partition, value, 6),
            ]
            df = spark.createDataFrame(data, schema=schema)
            df = df.withColumn("TIME", to_date(col("RAW_TIME")))

            return df

        asset_full_name = f"{schema}__{table_name}"
        bq_table_path = f"{schema}.{table_name}"

        bq_io_manager = bigquery_pyspark_io_manager.configured(SHARED_BUILDKITE_BQ_CONFIG)
        resource_defs = {"io_manager": bq_io_manager}

        materialize(
            [daily_partitioned],
            partition_key="2022-01-01",
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "1"}}}},
        )

        out_df = pandas_gbq.read_gbq(
            f"SELECT * FROM {bq_table_path}", project_id=SHARED_BUILDKITE_BQ_CONFIG["project"]
        )
        assert out_df["A"].tolist() == ["1", "1", "1"]

        materialize(
            [daily_partitioned],
            partition_key="2022-01-02",
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "2"}}}},
        )

        out_df = pandas_gbq.read_gbq(
            f"SELECT * FROM {bq_table_path}", project_id=SHARED_BUILDKITE_BQ_CONFIG["project"]
        )
        assert sorted(out_df["A"].tolist()) == ["1", "1", "1", "2", "2", "2"]

        materialize(
            [daily_partitioned],
            partition_key="2022-01-01",
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "3"}}}},
        )

        out_df = pandas_gbq.read_gbq(
            f"SELECT * FROM {bq_table_path}", project_id=SHARED_BUILDKITE_BQ_CONFIG["project"]
        )
        assert sorted(out_df["A"].tolist()) == ["2", "2", "2", "3", "3", "3"]


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE snowflake DB")
def test_static_partitioned_asset():
    schema = "BIGQUERY_IO_MANAGER_SCHEMA"
    with temporary_bigquery_table(
        schema_name=schema,
        column_str="foo string, quux integer",
    ) as table_name:

        @asset(
            partitions_def=StaticPartitionsDefinition(["red", "yellow", "blue"]),
            key_prefix=["SNOWFLAKE_IO_MANAGER_SCHEMA"],
            metadata={"partition_expr": "color"},
            config_schema={"value": str},
            name=table_name,
        )
        def static_partitioned(context) -> DataFrame:
            partition = context.asset_partition_key_for_output()
            value = context.op_config["value"]

            spark = SparkSession.builder.config(
                key="spark.jars.packages",
                value=BIGQUERY_JARS,
            ).getOrCreate()

            schema = StructType(
                [
                    StructField("COLOR", StringType()),
                    StructField("A", StringType()),
                    StructField("B", LongType()),
                ]
            )
            data = [(partition, value, 4), (partition, value, 5), (partition, value, 6)]
            df = spark.createDataFrame(data, schema=schema)
            return df

        asset_full_name = f"{schema}__{table_name}"
        bq_table_path = f"{schema}.{table_name}"

        bq_io_manager = bigquery_pyspark_io_manager.configured(SHARED_BUILDKITE_BQ_CONFIG)
        resource_defs = {"io_manager": bq_io_manager}

        materialize(
            [static_partitioned],
            partition_key="red",
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "1"}}}},
        )

        out_df = pandas_gbq.read_gbq(
            f"SELECT * FROM {bq_table_path}", project_id=SHARED_BUILDKITE_BQ_CONFIG["project"]
        )
        assert out_df["A"].tolist() == ["1", "1", "1"]

        materialize(
            [static_partitioned],
            partition_key="blue",
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "2"}}}},
        )

        out_df = pandas_gbq.read_gbq(
            f"SELECT * FROM {bq_table_path}", project_id=SHARED_BUILDKITE_BQ_CONFIG["project"]
        )
        assert sorted(out_df["A"].tolist()) == ["1", "1", "1", "2", "2", "2"]

        materialize(
            [static_partitioned],
            partition_key="red",
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "3"}}}},
        )

        out_df = pandas_gbq.read_gbq(
            f"SELECT * FROM {bq_table_path}", project_id=SHARED_BUILDKITE_BQ_CONFIG["project"]
        )
        assert sorted(out_df["A"].tolist()) == ["2", "2", "2", "3", "3", "3"]


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE snowflake DB")
def test_multi_partitioned_asset():
    schema = "BIGQUERY_IO_MANAGER_SCHEMA"
    with temporary_bigquery_table(
        schema_name=schema,
        column_str="foo string, quux integer",
    ) as table_name:

        @asset(
            partitions_def=MultiPartitionsDefinition(
                {
                    "time": DailyPartitionsDefinition(start_date="2022-01-01"),
                    "color": StaticPartitionsDefinition(["red", "yellow", "blue"]),
                }
            ),
            key_prefix=["SNOWFLAKE_IO_MANAGER_SCHEMA"],
            metadata={"partition_expr": {"time": "CAST(time as TIMESTAMP)", "color": "color"}},
            config_schema={"value": str},
            name=table_name,
        )
        def multi_partitioned(context) -> DataFrame:
            partition = context.partition_key.keys_by_dimension
            value = context.op_config["value"]

            spark = SparkSession.builder.config(
                key="spark.jars.packages",
                value=BIGQUERY_JARS,
            ).getOrCreate()

            schema = StructType(
                [
                    StructField("COLOR", StringType()),
                    StructField("RAW_TIME", StringType()),
                    StructField("A", StringType()),
                ]
            )
            data = [
                (partition["color"], partition["time"], value),
                (partition["color"], partition["time"], value),
                (partition["color"], partition["time"], value),
            ]
            df = spark.createDataFrame(data, schema=schema)
            df = df.withColumn("TIME", to_date(col("RAW_TIME")))

            return df

        asset_full_name = f"{schema}__{table_name}"
        bq_table_path = f"{schema}.{table_name}"

        bq_io_manager = bigquery_pyspark_io_manager.configured(SHARED_BUILDKITE_BQ_CONFIG)
        resource_defs = {"io_manager": bq_io_manager}

        materialize(
            [multi_partitioned],
            partition_key=MultiPartitionKey({"time": "2022-01-01", "color": "red"}),
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "1"}}}},
        )

        out_df = pandas_gbq.read_gbq(
            f"SELECT * FROM {bq_table_path}", project_id=SHARED_BUILDKITE_BQ_CONFIG["project"]
        )
        assert out_df["A"].tolist() == ["1", "1", "1"]

        materialize(
            [multi_partitioned],
            partition_key=MultiPartitionKey({"time": "2022-01-01", "color": "blue"}),
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "2"}}}},
        )

        out_df = pandas_gbq.read_gbq(
            f"SELECT * FROM {bq_table_path}", project_id=SHARED_BUILDKITE_BQ_CONFIG["project"]
        )
        assert sorted(out_df["A"].tolist()) == ["1", "1", "1", "2", "2", "2"]

        materialize(
            [multi_partitioned],
            partition_key=MultiPartitionKey({"time": "2022-01-02", "color": "red"}),
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "3"}}}},
        )

        out_df = pandas_gbq.read_gbq(
            f"SELECT * FROM {bq_table_path}", project_id=SHARED_BUILDKITE_BQ_CONFIG["project"]
        )
        assert sorted(out_df["A"].tolist()) == ["1", "1", "1", "2", "2", "2", "3", "3", "3"]

        materialize(
            [multi_partitioned],
            partition_key=MultiPartitionKey({"time": "2022-01-01", "color": "red"}),
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "4"}}}},
        )

        out_df = pandas_gbq.read_gbq(
            f"SELECT * FROM {bq_table_path}", project_id=SHARED_BUILDKITE_BQ_CONFIG["project"]
        )
        assert sorted(out_df["A"].tolist()) == ["2", "2", "2", "3", "3", "3", "4", "4", "4"]


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE snowflake DB")
def test_dynamic_partitions():
    schema = "BIGQUERY_IO_MANAGER_SCHEMA"
    with temporary_bigquery_table(
        schema_name=schema,
        column_str="foo string, quux integer",
    ) as table_name:
        dynamic_fruits = DynamicPartitionsDefinition(name="dynamic_fruits")

        @asset(
            partitions_def=dynamic_fruits,
            key_prefix=["SNOWFLAKE_IO_MANAGER_SCHEMA"],
            metadata={"partition_expr": "FRUIT"},
            config_schema={"value": str},
            name=table_name,
        )
        def dynamic_partitioned(context) -> DataFrame:
            partition = context.asset_partition_key_for_output()
            value = context.op_config["value"]

            spark = SparkSession.builder.config(
                key="spark.jars.packages",
                value=BIGQUERY_JARS,
            ).getOrCreate()

            schema = StructType(
                [
                    StructField("FRUIT", StringType()),
                    StructField("A", StringType()),
                ]
            )
            data = [
                (partition, value),
                (partition, value),
                (partition, value),
            ]
            df = spark.createDataFrame(data, schema=schema)
            return df

        asset_full_name = f"{schema}__{table_name}"
        bq_table_path = f"{schema}.{table_name}"

        bq_io_manager = bigquery_pyspark_io_manager.configured(SHARED_BUILDKITE_BQ_CONFIG)
        resource_defs = {"io_manager": bq_io_manager}

        with instance_for_test() as instance:
            dynamic_fruits.add_partitions(["apple"], instance)

            materialize(
                [dynamic_partitioned],
                partition_key="apple",
                resources=resource_defs,
                instance=instance,
                run_config={"ops": {asset_full_name: {"config": {"value": "1"}}}},
            )

            out_df = pandas_gbq.read_gbq(
                f"SELECT * FROM {bq_table_path}", project_id=SHARED_BUILDKITE_BQ_CONFIG["project"]
            )
            assert out_df["A"].tolist() == ["1", "1", "1"]

            dynamic_fruits.add_partitions(["orange"], instance)

            materialize(
                [dynamic_partitioned],
                partition_key="orange",
                resources=resource_defs,
                instance=instance,
                run_config={"ops": {asset_full_name: {"config": {"value": "2"}}}},
            )

            out_df = pandas_gbq.read_gbq(
                f"SELECT * FROM {bq_table_path}", project_id=SHARED_BUILDKITE_BQ_CONFIG["project"]
            )
            assert sorted(out_df["A"].tolist()) == ["1", "1", "1", "2", "2", "2"]

            materialize(
                [dynamic_partitioned],
                partition_key="apple",
                resources=resource_defs,
                instance=instance,
                run_config={"ops": {asset_full_name: {"config": {"value": "3"}}}},
            )

            out_df = pandas_gbq.read_gbq(
                f"SELECT * FROM {bq_table_path}", project_id=SHARED_BUILDKITE_BQ_CONFIG["project"]
            )
            assert sorted(out_df["A"].tolist()) == ["2", "2", "2", "3", "3", "3"]
