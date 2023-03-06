import logging
import os
import uuid
from contextlib import contextmanager
from typing import Iterator
from unittest.mock import patch

import pytest
from dagster import (
    AssetIn,
    AssetKey,
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
    TimeWindowPartitionMapping,
    asset,
    build_input_context,
    build_output_context,
    fs_io_manager,
    instance_for_test,
    job,
    materialize,
    op,
)
from dagster._core.storage.db_io_manager import TableSlice
from dagster_snowflake import build_snowflake_io_manager
from dagster_snowflake.resources import SnowflakeConnection
from dagster_snowflake_pyspark import SnowflakePySparkTypeHandler, snowflake_pyspark_io_manager
from pyspark.sql import DataFrame
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


SHARED_BUILDKITE_SNOWFLAKE_CONF = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT", ""),
    "user": "BUILDKITE",
    "password": os.getenv("SNOWFLAKE_BUILDKITE_PASSWORD", ""),
    "warehouse": "BUILDKITE",
}


@contextmanager
def temporary_snowflake_table(schema_name: str, db_name: str) -> Iterator[str]:
    snowflake_config = dict(database=db_name, **SHARED_BUILDKITE_SNOWFLAKE_CONF)
    table_name = "test_io_manager_" + str(uuid.uuid4()).replace("-", "_")
    with SnowflakeConnection(
        snowflake_config, logging.getLogger("temporary_snowflake_table")
    ).get_connection() as conn:
        try:
            yield table_name
        finally:
            conn.cursor().execute(f"drop table {schema_name}.{table_name}")


def test_handle_output(spark):
    with patch("pyspark.sql.DataFrame.write") as mock_write:
        handler = SnowflakePySparkTypeHandler()
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
            None,
        )

        assert metadata == {
            "dataframe_columns": MetadataValue.table_schema(
                TableSchema(columns=[TableColumn("col1", "string"), TableColumn("col2", "string")])
            ),
        }

        assert len(mock_write.method_calls) == 1


def test_load_input(spark):
    with patch("pyspark.sql.DataFrameReader.load") as mock_read:
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
                partition_dimensions=None,
            ),
            None,
        )
        assert mock_read.called


def test_build_snowflake_pyspark_io_manager():
    assert isinstance(
        build_snowflake_io_manager([SnowflakePySparkTypeHandler()]), IOManagerDefinition
    )
    # test wrapping decorator to make sure that works as expected
    assert isinstance(snowflake_pyspark_io_manager, IOManagerDefinition)


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE snowflake DB")
def test_io_manager_with_snowflake_pyspark(spark):
    with temporary_snowflake_table(
        schema_name="SNOWFLAKE_IO_MANAGER_SCHEMA",
        db_name="TEST_SNOWFLAKE_IO_MANAGER",
    ) as table_name:
        # Create a job with the temporary table name as an output, so that it will write to that table
        # and not interfere with other runs of this test

        @op(
            out={
                table_name: Out(
                    dagster_type=DataFrame, metadata={"schema": "SNOWFLAKE_IO_MANAGER_SCHEMA"}
                )
            },
        )
        def emit_pyspark_df(_):
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
                "io_manager": snowflake_pyspark_io_manager.configured(
                    {**SHARED_BUILDKITE_SNOWFLAKE_CONF, "database": "TEST_SNOWFLAKE_IO_MANAGER"}
                )
            }
        )
        def io_manager_test_pipeline():
            read_pyspark_df(emit_pyspark_df())

        res = io_manager_test_pipeline.execute_in_process()
        assert res.success


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE snowflake DB")
def test_time_window_partitioned_asset(spark):
    with temporary_snowflake_table(
        schema_name="SNOWFLAKE_IO_MANAGER_SCHEMA",
        db_name="TEST_SNOWFLAKE_IO_MANAGER",
    ) as table_name:
        partitions_def = DailyPartitionsDefinition(start_date="2022-01-01")

        @asset(
            partitions_def=partitions_def,
            metadata={"partition_expr": "time"},
            config_schema={"value": str},
            key_prefix="SNOWFLAKE_IO_MANAGER_SCHEMA",
            name=table_name,
        )
        def daily_partitioned(context) -> DataFrame:
            partition = context.asset_partition_key_for_output()
            value = context.op_config["value"]

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

        @asset(
            partitions_def=partitions_def,
            key_prefix="SNOWFLAKE_IO_MANAGER_SCHEMA",
            ins={"df": AssetIn(["SNOWFLAKE_IO_MANAGER_SCHEMA", table_name])},
            io_manager_key="fs_io",
        )
        def downstream_partitioned(df) -> None:
            # assert that we only get the columns created in daily_partitioned
            assert df.count() == 3

        asset_full_name = f"SNOWFLAKE_IO_MANAGER_SCHEMA__{table_name}"
        snowflake_table_path = f"SNOWFLAKE_IO_MANAGER_SCHEMA.{table_name}"

        snowflake_config = {
            **SHARED_BUILDKITE_SNOWFLAKE_CONF,
            "database": "TEST_SNOWFLAKE_IO_MANAGER",
        }
        snowflake_conn = SnowflakeConnection(
            snowflake_config, logging.getLogger("temporary_snowflake_table")
        )

        snowflake_io_manager = snowflake_pyspark_io_manager.configured(snowflake_config)
        resource_defs = {"io_manager": snowflake_io_manager, "fs_io": fs_io_manager}

        materialize(
            [daily_partitioned, downstream_partitioned],
            partition_key="2022-01-01",
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "1"}}}},
        )

        out_df = snowflake_conn.execute_query(
            f"SELECT * FROM {snowflake_table_path}", use_pandas_result=True, fetch_results=True
        )
        assert out_df["A"].tolist() == ["1", "1", "1"]

        materialize(
            [daily_partitioned, downstream_partitioned],
            partition_key="2022-01-02",
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "2"}}}},
        )

        out_df = snowflake_conn.execute_query(
            f"SELECT * FROM {snowflake_table_path}", use_pandas_result=True, fetch_results=True
        )
        assert sorted(out_df["A"].tolist()) == ["1", "1", "1", "2", "2", "2"]

        materialize(
            [daily_partitioned, downstream_partitioned],
            partition_key="2022-01-01",
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "3"}}}},
        )

        out_df = snowflake_conn.execute_query(
            f"SELECT * FROM {snowflake_table_path}", use_pandas_result=True, fetch_results=True
        )
        assert sorted(out_df["A"].tolist()) == ["2", "2", "2", "3", "3", "3"]


# @pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE snowflake DB")
def test_static_partitioned_asset(spark):
    with temporary_snowflake_table(
        schema_name="SNOWFLAKE_IO_MANAGER_SCHEMA",
        db_name="TEST_SNOWFLAKE_IO_MANAGER",
    ) as table_name:
        partitions_def = StaticPartitionsDefinition(["red", "yellow", "blue"])

        @asset(
            partitions_def=partitions_def,
            key_prefix=["SNOWFLAKE_IO_MANAGER_SCHEMA"],
            metadata={"partition_expr": "color"},
            config_schema={"value": str},
            name=table_name,
        )
        def static_partitioned(context) -> DataFrame:
            partition = context.asset_partition_key_for_output()
            value = context.op_config["value"]

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

        @asset(
            partitions_def=partitions_def,
            key_prefix="SNOWFLAKE_IO_MANAGER_SCHEMA",
            ins={"df": AssetIn(["SNOWFLAKE_IO_MANAGER_SCHEMA", table_name])},
            io_manager_key="fs_io",
        )
        def downstream_partitioned(df) -> None:
            # assert that we only get the columns created in static_partitioned
            assert df.count() == 3

        asset_full_name = f"SNOWFLAKE_IO_MANAGER_SCHEMA__{table_name}"
        snowflake_table_path = f"SNOWFLAKE_IO_MANAGER_SCHEMA.{table_name}"

        snowflake_config = {
            **SHARED_BUILDKITE_SNOWFLAKE_CONF,
            "database": "TEST_SNOWFLAKE_IO_MANAGER",
        }
        snowflake_conn = SnowflakeConnection(
            snowflake_config, logging.getLogger("temporary_snowflake_table")
        )

        snowflake_io_manager = snowflake_pyspark_io_manager.configured(snowflake_config)
        resource_defs = {"io_manager": snowflake_io_manager, "fs_io": fs_io_manager}
        materialize(
            [static_partitioned, downstream_partitioned],
            partition_key="red",
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "1"}}}},
        )

        out_df = snowflake_conn.execute_query(
            f"SELECT * FROM {snowflake_table_path}", use_pandas_result=True, fetch_results=True
        )
        assert out_df["A"].tolist() == ["1", "1", "1"]

        materialize(
            [static_partitioned, downstream_partitioned],
            partition_key="blue",
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "2"}}}},
        )

        out_df = snowflake_conn.execute_query(
            f"SELECT * FROM {snowflake_table_path}", use_pandas_result=True, fetch_results=True
        )
        assert sorted(out_df["A"].tolist()) == ["1", "1", "1", "2", "2", "2"]

        materialize(
            [static_partitioned, downstream_partitioned],
            partition_key="red",
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "3"}}}},
        )

        out_df = snowflake_conn.execute_query(
            f"SELECT * FROM {snowflake_table_path}", use_pandas_result=True, fetch_results=True
        )
        assert sorted(out_df["A"].tolist()) == ["2", "2", "2", "3", "3", "3"]


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE snowflake DB")
def test_multi_partitioned_asset(spark):
    with temporary_snowflake_table(
        schema_name="SNOWFLAKE_IO_MANAGER_SCHEMA",
        db_name="TEST_SNOWFLAKE_IO_MANAGER",
    ) as table_name:
        partitions_def = MultiPartitionsDefinition(
            {
                "time": DailyPartitionsDefinition(start_date="2022-01-01"),
                "color": StaticPartitionsDefinition(["red", "yellow", "blue"]),
            }
        )

        @asset(
            partitions_def=partitions_def,
            key_prefix=["SNOWFLAKE_IO_MANAGER_SCHEMA"],
            metadata={"partition_expr": {"time": "CAST(time as TIMESTAMP)", "color": "color"}},
            config_schema={"value": str},
            name=table_name,
        )
        def multi_partitioned(context) -> DataFrame:
            partition = context.partition_key.keys_by_dimension
            value = context.op_config["value"]

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

        @asset(
            partitions_def=partitions_def,
            key_prefix="SNOWFLAKE_IO_MANAGER_SCHEMA",
            ins={"df": AssetIn(["SNOWFLAKE_IO_MANAGER_SCHEMA", table_name])},
            io_manager_key="fs_io",
        )
        def downstream_partitioned(df) -> None:
            # assert that we only get the columns created in multi_partitioned
            assert df.count() == 3

        asset_full_name = f"SNOWFLAKE_IO_MANAGER_SCHEMA__{table_name}"
        snowflake_table_path = f"SNOWFLAKE_IO_MANAGER_SCHEMA.{table_name}"

        snowflake_config = {
            **SHARED_BUILDKITE_SNOWFLAKE_CONF,
            "database": "TEST_SNOWFLAKE_IO_MANAGER",
        }
        snowflake_conn = SnowflakeConnection(
            snowflake_config, logging.getLogger("temporary_snowflake_table")
        )

        snowflake_io_manager = snowflake_pyspark_io_manager.configured(snowflake_config)
        resource_defs = {"io_manager": snowflake_io_manager, "fs_io": fs_io_manager}

        materialize(
            [multi_partitioned, downstream_partitioned],
            partition_key=MultiPartitionKey({"time": "2022-01-01", "color": "red"}),
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "1"}}}},
        )

        out_df = snowflake_conn.execute_query(
            f"SELECT * FROM {snowflake_table_path}", use_pandas_result=True, fetch_results=True
        )
        assert out_df["A"].tolist() == ["1", "1", "1"]

        materialize(
            [multi_partitioned, downstream_partitioned],
            partition_key=MultiPartitionKey({"time": "2022-01-01", "color": "blue"}),
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "2"}}}},
        )

        out_df = snowflake_conn.execute_query(
            f"SELECT * FROM {snowflake_table_path}", use_pandas_result=True, fetch_results=True
        )
        assert sorted(out_df["A"].tolist()) == ["1", "1", "1", "2", "2", "2"]

        materialize(
            [multi_partitioned, downstream_partitioned],
            partition_key=MultiPartitionKey({"time": "2022-01-02", "color": "red"}),
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "3"}}}},
        )

        out_df = snowflake_conn.execute_query(
            f"SELECT * FROM {snowflake_table_path}", use_pandas_result=True, fetch_results=True
        )
        assert sorted(out_df["A"].tolist()) == ["1", "1", "1", "2", "2", "2", "3", "3", "3"]

        materialize(
            [multi_partitioned, downstream_partitioned],
            partition_key=MultiPartitionKey({"time": "2022-01-01", "color": "red"}),
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "4"}}}},
        )

        out_df = snowflake_conn.execute_query(
            f"SELECT * FROM {snowflake_table_path}", use_pandas_result=True, fetch_results=True
        )
        assert sorted(out_df["A"].tolist()) == ["2", "2", "2", "3", "3", "3", "4", "4", "4"]


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE snowflake DB")
def test_dynamic_partitions(spark):
    with temporary_snowflake_table(
        schema_name="SNOWFLAKE_IO_MANAGER_SCHEMA",
        db_name="TEST_SNOWFLAKE_IO_MANAGER",
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

        @asset(
            partitions_def=dynamic_fruits,
            key_prefix="SNOWFLAKE_IO_MANAGER_SCHEMA",
            ins={"df": AssetIn(["SNOWFLAKE_IO_MANAGER_SCHEMA", table_name])},
            io_manager_key="fs_io",
        )
        def downstream_partitioned(df) -> None:
            # assert that we only get the columns created in dynamic_partitioned
            assert df.count() == 3

        asset_full_name = f"SNOWFLAKE_IO_MANAGER_SCHEMA__{table_name}"
        snowflake_table_path = f"SNOWFLAKE_IO_MANAGER_SCHEMA.{table_name}"

        snowflake_config = {
            **SHARED_BUILDKITE_SNOWFLAKE_CONF,
            "database": "TEST_SNOWFLAKE_IO_MANAGER",
        }
        snowflake_conn = SnowflakeConnection(
            snowflake_config, logging.getLogger("temporary_snowflake_table")
        )

        snowflake_io_manager = snowflake_pyspark_io_manager.configured(snowflake_config)
        resource_defs = {"io_manager": snowflake_io_manager, "fs_io": fs_io_manager}

        with instance_for_test() as instance:
            instance.add_dynamic_partitions(dynamic_fruits.name, ["apple"])

            materialize(
                [dynamic_partitioned, downstream_partitioned],
                partition_key="apple",
                resources=resource_defs,
                instance=instance,
                run_config={"ops": {asset_full_name: {"config": {"value": "1"}}}},
            )

            out_df = snowflake_conn.execute_query(
                f"SELECT * FROM {snowflake_table_path}", use_pandas_result=True, fetch_results=True
            )
            assert out_df["A"].tolist() == ["1", "1", "1"]

            instance.add_dynamic_partitions(dynamic_fruits.name, ["orange"])

            materialize(
                [dynamic_partitioned, downstream_partitioned],
                partition_key="orange",
                resources=resource_defs,
                instance=instance,
                run_config={"ops": {asset_full_name: {"config": {"value": "2"}}}},
            )

            out_df = snowflake_conn.execute_query(
                f"SELECT * FROM {snowflake_table_path}", use_pandas_result=True, fetch_results=True
            )
            assert sorted(out_df["A"].tolist()) == ["1", "1", "1", "2", "2", "2"]

            materialize(
                [dynamic_partitioned, downstream_partitioned],
                partition_key="apple",
                resources=resource_defs,
                instance=instance,
                run_config={"ops": {asset_full_name: {"config": {"value": "3"}}}},
            )

            out_df = snowflake_conn.execute_query(
                f"SELECT * FROM {snowflake_table_path}", use_pandas_result=True, fetch_results=True
            )
            assert sorted(out_df["A"].tolist()) == ["2", "2", "2", "3", "3", "3"]


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE snowflake DB")
def test_self_dependent_asset():
    schema = "SNOWFLAKE_IO_MANAGER_SCHEMA"
    with temporary_snowflake_table(
        schema_name=schema,
        column_str=(
            "RAW_START string, RAW_END string, START TIMESTAMP_NTZ(9), END TIMESTAMP_NTZ(9), A"
            " string"
        ),
    ) as table_name:
        daily_partitions = DailyPartitionsDefinition(start_date="2023-01-01")

        @asset(
            partitions_def=daily_partitions,
            key_prefix=schema,
            ins={
                "self_dependent_asset": AssetIn(
                    key=AssetKey(["my_schema", "self_dependent_asset"]),
                    partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
                ),
            },
            metadata={
                "partition_expr": "start",
            },
            config_schema={"value": str},
            name=table_name,
        )
        def self_dependent_asset(context, self_dependent_asset: DataFrame) -> DataFrame:
            start, end = context.output_asset_partitions_time_window()
            value = context.op_config["value"]
            spark = SparkSession.builder.config(
                key="spark.jars.packages",
                value=SNOWFLAKE_JARS,
            ).getOrCreate()

            schema = StructType(
                [
                    StructField("RAW_START", StringType()),
                    StructField("RAW_END", StringType()),
                    StructField("A", StringType()),
                ]
            )
            data = [
                (start, end, value),
                (start, end, value),
                (start, end, value),
            ]
            df = spark.createDataFrame(data, schema=schema)
            df = df.withColumn("START", to_date(col("RAW_START")))
            df = df.withColumn("END", to_date(col("RAW_END")))

            return df

        asset_full_name = f"{schema}__{table_name}"
        snowflake_table_path = f"{schema}.{table_name}"

        snowflake_config = {
            **SHARED_BUILDKITE_SNOWFLAKE_CONF,
            "database": "TEST_SNOWFLAKE_IO_MANAGER",
        }
        snowflake_conn = SnowflakeConnection(
            snowflake_config, logging.getLogger("temporary_snowflake_table")
        )

        snowflake_io_manager = snowflake_pyspark_io_manager.configured(snowflake_config)
        resource_defs = {"io_manager": snowflake_io_manager}

        materialize(
            [self_dependent_asset],
            partition_key="2023-01-01",
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "1"}}}},
        )

        out_df = snowflake_conn.execute_query(
            f"SELECT * FROM {snowflake_table_path}", use_pandas_result=True
        )
        assert sorted(out_df["A"].tolist()) == ["1", "1", "1"]
