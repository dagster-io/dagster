import os
import uuid
from contextlib import contextmanager
from typing import Iterator

import pandas as pd
import pandas_gbq
import pytest
from dagster import (
    AssetIn,
    DailyPartitionsDefinition,
    DynamicPartitionsDefinition,
    MultiPartitionKey,
    MultiPartitionsDefinition,
    Out,
    StaticPartitionsDefinition,
    asset,
    fs_io_manager,
    instance_for_test,
    job,
    materialize,
    op,
)
from dagster_gcp_pandas import bigquery_pandas_io_manager
from google.cloud import bigquery

IS_BUILDKITE = os.getenv("BUILDKITE") is not None

SHARED_BUILDKITE_BQ_CONFIG = {
    "project": os.getenv("GCP_PROJECT_ID"),
}


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


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE bigquery DB")
def test_io_manager_with_bigquery_pandas():
    schema = "BIGQUERY_IO_MANAGER_SCHEMA"
    with temporary_bigquery_table(
        schema_name=schema,
        column_str="FOO string, QUUX int",
    ) as table_name:
        # Create a job with the temporary table name as an output, so that it will write to that table
        # and not interfere with other runs of this test

        @op(
            out={
                table_name: Out(
                    io_manager_key="bigquery",
                    metadata={"schema": schema},
                )
            }
        )
        def emit_pandas_df() -> pd.DataFrame:
            return pd.DataFrame({"foo": ["bar", "baz"], "quux": [1, 2]})

        @op
        def read_pandas_df(df: pd.DataFrame) -> None:
            assert set(df.columns) == {"foo", "quux"}
            assert len(df.index) == 2

        @job(
            resource_defs={"bigquery": bigquery_pandas_io_manager},
            config={
                "resources": {
                    "bigquery": {
                        "config": {
                            **SHARED_BUILDKITE_BQ_CONFIG,
                        }
                    }
                }
            },
        )
        def io_manager_test_pipeline():
            read_pandas_df(emit_pandas_df())

        res = io_manager_test_pipeline.execute_in_process()
        assert res.success

        # run again to ensure table is properly deleted
        res = io_manager_test_pipeline.execute_in_process()
        assert res.success


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE bigquery DB")
def test_io_manager_with_snowflake_pandas_timestamp_data():
    schema = "BIGQUERY_IO_MANAGER_SCHEMA"
    with temporary_bigquery_table(
        schema_name=schema,
        column_str="FOO string, DATE TIMESTAMP",
    ) as table_name:
        time_df = pd.DataFrame(
            {
                "foo": ["bar", "baz"],
                "date": [
                    pd.Timestamp("2017-01-01T12:30:45.350"),
                    pd.Timestamp("2017-02-01T12:30:45.350"),
                ],
            }
        )

        @op(out={table_name: Out(io_manager_key="bigquery", metadata={"schema": schema})})
        def emit_time_df(_):
            return time_df

        @op
        def read_time_df(df: pd.DataFrame):
            assert set(df.columns) == {"foo", "date"}
            assert (df["date"] == time_df["date"].dt.tz_localize("UTC")).all()

        @job(
            resource_defs={"bigquery": bigquery_pandas_io_manager},
            config={
                "resources": {
                    "bigquery": {
                        "config": {
                            **SHARED_BUILDKITE_BQ_CONFIG,
                        }
                    }
                }
            },
        )
        def io_manager_timestamp_test_job():
            read_time_df(emit_time_df())

        res = io_manager_timestamp_test_job.execute_in_process()
        assert res.success


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE bigquery DB")
def test_time_window_partitioned_asset():
    schema = "BIGQUERY_IO_MANAGER_SCHEMA"
    with temporary_bigquery_table(
        schema_name=schema,
        column_str="TIME TIMESTAMP, A string, B int",
    ) as table_name:
        partitions_def = DailyPartitionsDefinition(start_date="2022-01-01")

        @asset(
            partitions_def=partitions_def,
            metadata={"partition_expr": "time"},
            config_schema={"value": str},
            key_prefix=schema,
            name=table_name,
        )
        def daily_partitioned(context) -> pd.DataFrame:
            partition = pd.Timestamp(context.asset_partition_key_for_output())
            value = context.op_config["value"]

            return pd.DataFrame(
                {
                    "TIME": [partition, partition, partition],
                    "A": [value, value, value],
                    "B": [4, 5, 6],
                }
            )

        @asset(
            partitions_def=partitions_def,
            key_prefix=schema,
            ins={"df": AssetIn([schema, table_name])},
            io_manager_key="fs_io",
        )
        def downstream_partitioned(df: pd.DataFrame) -> None:
            # assert that we only get the columns created in daily_partitioned
            assert len(df.index) == 3

        asset_full_name = f"{schema}__{table_name}"
        bq_table_path = f"{schema}.{table_name}"

        bq_io_manager = bigquery_pandas_io_manager.configured(SHARED_BUILDKITE_BQ_CONFIG)
        resource_defs = {"io_manager": bq_io_manager, "fs_io": fs_io_manager}

        materialize(
            [daily_partitioned, downstream_partitioned],
            partition_key="2022-01-01",
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "1"}}}},
        )

        out_df = pandas_gbq.read_gbq(
            f"SELECT * FROM {bq_table_path}", project_id=SHARED_BUILDKITE_BQ_CONFIG["project"]
        )

        assert out_df["A"].tolist() == ["1", "1", "1"]

        materialize(
            [daily_partitioned, downstream_partitioned],
            partition_key="2022-01-02",
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "2"}}}},
        )

        out_df = pandas_gbq.read_gbq(
            f"SELECT * FROM {bq_table_path}", project_id=SHARED_BUILDKITE_BQ_CONFIG["project"]
        )
        assert sorted(out_df["A"].tolist()) == ["1", "1", "1", "2", "2", "2"]

        materialize(
            [daily_partitioned, downstream_partitioned],
            partition_key="2022-01-01",
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "3"}}}},
        )

        out_df = pandas_gbq.read_gbq(
            f"SELECT * FROM {bq_table_path}", project_id=SHARED_BUILDKITE_BQ_CONFIG["project"]
        )
        assert sorted(out_df["A"].tolist()) == ["2", "2", "2", "3", "3", "3"]


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE bigquery DB")
def test_static_partitioned_asset():
    schema = "BIGQUERY_IO_MANAGER_SCHEMA"
    with temporary_bigquery_table(
        schema_name=schema,
        column_str=" COLOR string, A string, B int",
    ) as table_name:
        partitions_def = StaticPartitionsDefinition(["red", "yellow", "blue"])

        @asset(
            partitions_def=partitions_def,
            key_prefix=[schema],
            metadata={"partition_expr": "color"},
            config_schema={"value": str},
            name=table_name,
        )
        def static_partitioned(context) -> pd.DataFrame:
            partition = context.asset_partition_key_for_output()
            value = context.op_config["value"]
            return pd.DataFrame(
                {
                    "COLOR": [partition, partition, partition],
                    "A": [value, value, value],
                    "B": [4, 5, 6],
                }
            )

        @asset(
            partitions_def=partitions_def,
            key_prefix=schema,
            ins={"df": AssetIn([schema, table_name])},
            io_manager_key="fs_io",
        )
        def downstream_partitioned(df: pd.DataFrame) -> None:
            # assert that we only get the columns created in static_partitioned
            assert len(df.index) == 3

        asset_full_name = f"{schema}__{table_name}"
        bq_table_path = f"{schema}.{table_name}"

        bq_io_manager = bigquery_pandas_io_manager.configured(SHARED_BUILDKITE_BQ_CONFIG)
        resource_defs = {"io_manager": bq_io_manager, "fs_io": fs_io_manager}

        materialize(
            [static_partitioned, downstream_partitioned],
            partition_key="red",
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "1"}}}},
        )

        out_df = pandas_gbq.read_gbq(
            f"SELECT * FROM {bq_table_path}", project_id=SHARED_BUILDKITE_BQ_CONFIG["project"]
        )
        assert out_df["A"].tolist() == ["1", "1", "1"]

        materialize(
            [static_partitioned, downstream_partitioned],
            partition_key="blue",
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "2"}}}},
        )

        out_df = pandas_gbq.read_gbq(
            f"SELECT * FROM {bq_table_path}", project_id=SHARED_BUILDKITE_BQ_CONFIG["project"]
        )
        assert sorted(out_df["A"].tolist()) == ["1", "1", "1", "2", "2", "2"]

        materialize(
            [static_partitioned, downstream_partitioned],
            partition_key="red",
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "3"}}}},
        )

        out_df = pandas_gbq.read_gbq(
            f"SELECT * FROM {bq_table_path}", project_id=SHARED_BUILDKITE_BQ_CONFIG["project"]
        )
        assert sorted(out_df["A"].tolist()) == ["2", "2", "2", "3", "3", "3"]


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE bigquery DB")
def test_multi_partitioned_asset():
    schema = "BIGQUERY_IO_MANAGER_SCHEMA"
    with temporary_bigquery_table(
        schema_name=schema,
        column_str=" COLOR string, TIME TIMESTAMP, A string",
    ) as table_name:
        partitions_def = MultiPartitionsDefinition(
            {
                "time": DailyPartitionsDefinition(start_date="2022-01-01"),
                "color": StaticPartitionsDefinition(["red", "yellow", "blue"]),
            }
        )

        @asset(
            partitions_def=partitions_def,
            key_prefix=[schema],
            metadata={"partition_expr": {"time": "TIME", "color": "COLOR"}},
            config_schema={"value": str},
            name=table_name,
        )
        def multi_partitioned(context) -> pd.DataFrame:
            partition = context.partition_key.keys_by_dimension
            partition_time = pd.Timestamp(partition["time"])
            partition_color = partition["color"]
            value = context.op_config["value"]

            return pd.DataFrame(
                {
                    "COLOR": [partition_color, partition_color, partition_color],
                    "TIME": [partition_time, partition_time, partition_time],
                    "A": [value, value, value],
                }
            )

        @asset(
            partitions_def=partitions_def,
            key_prefix=schema,
            ins={"df": AssetIn([schema, table_name])},
            io_manager_key="fs_io",
        )
        def downstream_partitioned(df: pd.DataFrame) -> None:
            # assert that we only get the columns created in multi_partitioned
            assert len(df.index) == 3

        asset_full_name = f"{schema}__{table_name}"
        bq_table_path = f"{schema}.{table_name}"

        bq_io_manager = bigquery_pandas_io_manager.configured(SHARED_BUILDKITE_BQ_CONFIG)
        resource_defs = {"io_manager": bq_io_manager, "fs_io": fs_io_manager}

        materialize(
            [multi_partitioned, downstream_partitioned],
            partition_key=MultiPartitionKey({"time": "2022-01-01", "color": "red"}),
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "1"}}}},
        )

        out_df = pandas_gbq.read_gbq(
            f"SELECT * FROM {bq_table_path}", project_id=SHARED_BUILDKITE_BQ_CONFIG["project"]
        )
        assert out_df["A"].tolist() == ["1", "1", "1"]

        materialize(
            [multi_partitioned, downstream_partitioned],
            partition_key=MultiPartitionKey({"time": "2022-01-01", "color": "blue"}),
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "2"}}}},
        )

        out_df = pandas_gbq.read_gbq(
            f"SELECT * FROM {bq_table_path}", project_id=SHARED_BUILDKITE_BQ_CONFIG["project"]
        )
        assert sorted(out_df["A"].tolist()) == ["1", "1", "1", "2", "2", "2"]

        materialize(
            [multi_partitioned, downstream_partitioned],
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


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE bigquery DB")
def test_dynamic_partitioned_asset():
    schema = "BIGQUERY_IO_MANAGER_SCHEMA"
    with temporary_bigquery_table(
        schema_name=schema,
        column_str=" FRUIT string, A string",
    ) as table_name:
        dynamic_fruits = DynamicPartitionsDefinition(name="dynamic_fruits")

        @asset(
            partitions_def=dynamic_fruits,
            key_prefix=[schema],
            metadata={"partition_expr": "FRUIT"},
            config_schema={"value": str},
            name=table_name,
        )
        def dynamic_partitioned(context) -> pd.DataFrame:
            partition = context.asset_partition_key_for_output()
            value = context.op_config["value"]
            return pd.DataFrame(
                {
                    "fruit": [partition, partition, partition],
                    "a": [value, value, value],
                }
            )

        @asset(
            partitions_def=dynamic_fruits,
            key_prefix=schema,
            ins={"df": AssetIn([schema, table_name])},
            io_manager_key="fs_io",
        )
        def downstream_partitioned(df: pd.DataFrame) -> None:
            # assert that we only get the columns created in dynamic_partitioned
            assert len(df.index) == 3

        asset_full_name = f"{schema}__{table_name}"
        bq_table_path = f"{schema}.{table_name}"

        bq_io_manager = bigquery_pandas_io_manager.configured(SHARED_BUILDKITE_BQ_CONFIG)
        resource_defs = {"io_manager": bq_io_manager, "fs_io": fs_io_manager}

        with instance_for_test() as instance:
            dynamic_fruits.add_partitions(["apple"], instance)

            materialize(
                [dynamic_partitioned, downstream_partitioned],
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
                [dynamic_partitioned, downstream_partitioned],
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
                [dynamic_partitioned, downstream_partitioned],
                partition_key="apple",
                resources=resource_defs,
                instance=instance,
                run_config={"ops": {asset_full_name: {"config": {"value": "3"}}}},
            )

            out_df = pandas_gbq.read_gbq(
                f"SELECT * FROM {bq_table_path}", project_id=SHARED_BUILDKITE_BQ_CONFIG["project"]
            )
            assert sorted(out_df["A"].tolist()) == ["2", "2", "2", "3", "3", "3"]
