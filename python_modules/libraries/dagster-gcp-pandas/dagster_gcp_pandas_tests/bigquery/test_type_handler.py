import os
import uuid
from contextlib import contextmanager
from typing import Iterator, Optional, cast

import pandas as pd
import pandas_gbq
import pytest
from dagster import (
    AssetExecutionContext,
    AssetIn,
    AssetKey,
    DailyPartitionsDefinition,
    Definitions,
    DynamicPartitionsDefinition,
    EnvVar,
    MetadataValue,
    MultiPartitionKey,
    MultiPartitionsDefinition,
    Out,
    StaticPartitionsDefinition,
    TimeWindowPartitionMapping,
    asset,
    fs_io_manager,
    instance_for_test,
    job,
    materialize,
    op,
)
from dagster._core.definitions.metadata.metadata_value import IntMetadataValue
from dagster_gcp_pandas import BigQueryPandasIOManager, bigquery_pandas_io_manager
from google.cloud import bigquery

IS_BUILDKITE = os.getenv("BUILDKITE") is not None

SHARED_BUILDKITE_BQ_CONFIG = {
    "project": os.getenv("GCP_PROJECT_ID"),
}

SCHEMA = "BIGQUERY_IO_MANAGER_SCHEMA"

pythonic_bigquery_io_manager = BigQueryPandasIOManager(
    project=EnvVar("GCP_PROJECT_ID"),
)
old_bigquery_io_manager = bigquery_pandas_io_manager.configured(SHARED_BUILDKITE_BQ_CONFIG)


@contextmanager
def temporary_bigquery_table(schema_name: Optional[str]) -> Iterator[str]:
    bq_client = bigquery.Client(
        project=SHARED_BUILDKITE_BQ_CONFIG["project"],
    )
    table_name = "test_io_manager_" + str(uuid.uuid4()).replace("-", "_")
    try:
        yield table_name
    finally:
        bq_client.query(
            f"drop table {SHARED_BUILDKITE_BQ_CONFIG['project']}.{schema_name}.{table_name}"
        ).result()


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE snowflake DB")
@pytest.mark.integration
def test_io_manager_asset_metadata() -> None:
    with temporary_bigquery_table(schema_name=SCHEMA) as table_name:

        @asset(key_prefix=SCHEMA, name=table_name)
        def my_pandas_df() -> pd.DataFrame:
            return pd.DataFrame({"foo": ["bar", "baz"], "quux": [1, 2]})

        defs = Definitions(
            assets=[my_pandas_df], resources={"io_manager": pythonic_bigquery_io_manager}
        )

        res = defs.get_implicit_global_asset_job_def().execute_in_process()
        assert res.success

        mats = res.get_asset_materialization_events()
        assert len(mats) == 1
        mat = mats[0]

        assert mat.materialization.metadata["dagster/relation_identifier"] == MetadataValue.text(
            f"{os.getenv('GCP_PROJECT_ID')}.{SCHEMA}.{table_name}"
        )


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE bigquery DB")
@pytest.mark.parametrize("io_manager", [(old_bigquery_io_manager), (pythonic_bigquery_io_manager)])
@pytest.mark.integration
def test_io_manager_with_bigquery_pandas(io_manager):
    with temporary_bigquery_table(schema_name=SCHEMA) as table_name:
        # Create a job with the temporary table name as an output, so that it will write to that table
        # and not interfere with other runs of this test

        @op(
            out={
                table_name: Out(
                    io_manager_key="bigquery",
                    metadata={"schema": SCHEMA},
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
            resource_defs={"bigquery": io_manager},
        )
        def io_manager_test_job():
            read_pandas_df(emit_pandas_df())

        res = io_manager_test_job.execute_in_process()
        assert res.success

        # run again to ensure table is properly deleted
        res = io_manager_test_job.execute_in_process()
        assert res.success


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE bigquery DB")
@pytest.mark.parametrize("io_manager", [(old_bigquery_io_manager), (pythonic_bigquery_io_manager)])
@pytest.mark.integration
def test_io_manager_with_timestamp_conversion(io_manager):
    with temporary_bigquery_table(schema_name=SCHEMA) as table_name:
        time_df = pd.DataFrame(
            {
                "foo": ["bar", "baz"],
                "date": [
                    pd.Timestamp("2017-01-01T12:30:45.350"),
                    pd.Timestamp("2017-02-01T12:30:45.350"),
                ],
            }
        )

        @op(out={table_name: Out(io_manager_key="bigquery", metadata={"schema": SCHEMA})})
        def emit_time_df(_):
            return time_df

        @op
        def read_time_df(df: pd.DataFrame):
            assert set(df.columns) == {"foo", "date"}
            assert (df["date"] == time_df["date"]).all()

        @job(
            resource_defs={"bigquery": io_manager},
        )
        def io_manager_timestamp_test_job():
            read_time_df(emit_time_df())

        res = io_manager_timestamp_test_job.execute_in_process()
        assert res.success


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE bigquery DB")
@pytest.mark.parametrize("io_manager", [(old_bigquery_io_manager), (pythonic_bigquery_io_manager)])
@pytest.mark.integration
def test_time_window_partitioned_asset(io_manager):
    with temporary_bigquery_table(schema_name=SCHEMA) as table_name:
        partitions_def = DailyPartitionsDefinition(start_date="2022-01-01")

        @asset(
            partitions_def=partitions_def,
            metadata={"partition_expr": "time"},
            config_schema={"value": str},
            key_prefix=SCHEMA,
            name=table_name,
        )
        def daily_partitioned(context: AssetExecutionContext) -> pd.DataFrame:
            partition = pd.Timestamp(context.partition_key)
            value = context.op_execution_context.op_config["value"]

            return pd.DataFrame(
                {
                    "TIME": [partition, partition, partition],
                    "A": [value, value, value],
                    "B": [4, 5, 6],
                }
            )

        @asset(
            partitions_def=partitions_def,
            key_prefix=SCHEMA,
            ins={"df": AssetIn([SCHEMA, table_name])},
            io_manager_key="fs_io",
        )
        def downstream_partitioned(df: pd.DataFrame) -> None:
            # assert that we only get the columns created in daily_partitioned
            assert len(df.index) == 3

        asset_full_name = f"{SCHEMA}__{table_name}"
        bq_table_path = f"{SCHEMA}.{table_name}"

        resource_defs = {"io_manager": io_manager, "fs_io": fs_io_manager}

        result = materialize(
            [daily_partitioned, downstream_partitioned],
            partition_key="2022-01-01",
            resources=resource_defs,
            run_config={"ops": {asset_full_name: {"config": {"value": "1"}}}},
        )

        materialization = next(
            event
            for event in result.all_events
            if event.event_type_value == "ASSET_MATERIALIZATION"
        )
        meta = materialization.materialization.metadata["dagster/partition_row_count"]
        assert cast(IntMetadataValue, meta).value == 3

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
@pytest.mark.parametrize("io_manager", [(old_bigquery_io_manager), (pythonic_bigquery_io_manager)])
@pytest.mark.integration
def test_static_partitioned_asset(io_manager):
    with temporary_bigquery_table(schema_name=SCHEMA) as table_name:
        partitions_def = StaticPartitionsDefinition(["red", "yellow", "blue"])

        @asset(
            partitions_def=partitions_def,
            key_prefix=[SCHEMA],
            metadata={"partition_expr": "color"},
            config_schema={"value": str},
            name=table_name,
        )
        def static_partitioned(context: AssetExecutionContext) -> pd.DataFrame:
            partition = context.partition_key
            value = context.op_execution_context.op_config["value"]
            return pd.DataFrame(
                {
                    "COLOR": [partition, partition, partition],
                    "A": [value, value, value],
                    "B": [4, 5, 6],
                }
            )

        @asset(
            partitions_def=partitions_def,
            key_prefix=SCHEMA,
            ins={"df": AssetIn([SCHEMA, table_name])},
            io_manager_key="fs_io",
        )
        def downstream_partitioned(df: pd.DataFrame) -> None:
            # assert that we only get the columns created in static_partitioned
            assert len(df.index) == 3

        asset_full_name = f"{SCHEMA}__{table_name}"
        bq_table_path = f"{SCHEMA}.{table_name}"

        resource_defs = {"io_manager": io_manager, "fs_io": fs_io_manager}

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
@pytest.mark.parametrize("io_manager", [(old_bigquery_io_manager), (pythonic_bigquery_io_manager)])
@pytest.mark.integration
def test_multi_partitioned_asset(io_manager):
    with temporary_bigquery_table(schema_name=SCHEMA) as table_name:
        partitions_def = MultiPartitionsDefinition(
            {
                "time": DailyPartitionsDefinition(start_date="2022-01-01"),
                "color": StaticPartitionsDefinition(["red", "yellow", "blue"]),
            }
        )

        @asset(
            partitions_def=partitions_def,
            key_prefix=[SCHEMA],
            metadata={"partition_expr": {"time": "TIME", "color": "COLOR"}},
            config_schema={"value": str},
            name=table_name,
        )
        def multi_partitioned(context) -> pd.DataFrame:
            partition = context.partition_key.keys_by_dimension
            partition_time = pd.Timestamp(partition["time"])
            partition_color = partition["color"]
            value = context.op_execution_context.op_config["value"]

            return pd.DataFrame(
                {
                    "COLOR": [partition_color, partition_color, partition_color],
                    "TIME": [partition_time, partition_time, partition_time],
                    "A": [value, value, value],
                }
            )

        @asset(
            partitions_def=partitions_def,
            key_prefix=SCHEMA,
            ins={"df": AssetIn([SCHEMA, table_name])},
            io_manager_key="fs_io",
        )
        def downstream_partitioned(df: pd.DataFrame) -> None:
            # assert that we only get the columns created in multi_partitioned
            assert len(df.index) == 3

        asset_full_name = f"{SCHEMA}__{table_name}"
        bq_table_path = f"{SCHEMA}.{table_name}"

        resource_defs = {"io_manager": io_manager, "fs_io": fs_io_manager}

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
@pytest.mark.parametrize("io_manager", [(old_bigquery_io_manager), (pythonic_bigquery_io_manager)])
@pytest.mark.integration
def test_dynamic_partitioned_asset(io_manager):
    with temporary_bigquery_table(schema_name=SCHEMA) as table_name:
        dynamic_fruits = DynamicPartitionsDefinition(name="dynamic_fruits")

        @asset(
            partitions_def=dynamic_fruits,
            key_prefix=[SCHEMA],
            metadata={"partition_expr": "FRUIT"},
            config_schema={"value": str},
            name=table_name,
        )
        def dynamic_partitioned(context: AssetExecutionContext) -> pd.DataFrame:
            partition = context.partition_key
            value = context.op_execution_context.op_config["value"]
            return pd.DataFrame(
                {
                    "fruit": [partition, partition, partition],
                    "a": [value, value, value],
                }
            )

        @asset(
            partitions_def=dynamic_fruits,
            key_prefix=SCHEMA,
            ins={"df": AssetIn([SCHEMA, table_name])},
            io_manager_key="fs_io",
        )
        def downstream_partitioned(df: pd.DataFrame) -> None:
            # assert that we only get the columns created in dynamic_partitioned
            assert len(df.index) == 3

        asset_full_name = f"{SCHEMA}__{table_name}"
        bq_table_path = f"{SCHEMA}.{table_name}"

        resource_defs = {"io_manager": io_manager, "fs_io": fs_io_manager}

        with instance_for_test() as instance:
            instance.add_dynamic_partitions(dynamic_fruits.name, ["apple"])

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

            instance.add_dynamic_partitions(dynamic_fruits.name, ["orange"])

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


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE bigquery DB")
@pytest.mark.parametrize("io_manager", [(old_bigquery_io_manager), (pythonic_bigquery_io_manager)])
@pytest.mark.integration
def test_self_dependent_asset(io_manager):
    with temporary_bigquery_table(
        schema_name=SCHEMA,
    ) as table_name:
        daily_partitions = DailyPartitionsDefinition(start_date="2023-01-01")

        @asset(
            partitions_def=daily_partitions,
            key_prefix=SCHEMA,
            ins={
                "self_dependent_asset": AssetIn(
                    key=AssetKey([SCHEMA, table_name]),
                    partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
                ),
            },
            metadata={
                "partition_expr": "TIMESTAMP(key)",
            },
            config_schema={"value": str, "last_partition_key": str},
            name=table_name,
        )
        def self_dependent_asset(
            context: AssetExecutionContext, self_dependent_asset: pd.DataFrame
        ) -> pd.DataFrame:
            key = context.partition_key

            if not self_dependent_asset.empty:
                assert len(self_dependent_asset.index) == 3
                assert (
                    self_dependent_asset["key"]
                    == context.op_execution_context.op_config["last_partition_key"]
                ).all()
            else:
                assert context.op_execution_context.op_config["last_partition_key"] == "NA"
            value = context.op_execution_context.op_config["value"]
            pd_df = pd.DataFrame(
                {
                    "key": [key, key, key],
                    "a": [value, value, value],
                }
            )

            return pd_df

        asset_full_name = f"{SCHEMA}__{table_name}"
        bq_table_path = f"{SCHEMA}.{table_name}"

        resource_defs = {"io_manager": io_manager}

        materialize(
            [self_dependent_asset],
            partition_key="2023-01-01",
            resources=resource_defs,
            run_config={
                "ops": {asset_full_name: {"config": {"value": "1", "last_partition_key": "NA"}}}
            },
        )

        out_df = pandas_gbq.read_gbq(
            f"SELECT * FROM {bq_table_path}", project_id=SHARED_BUILDKITE_BQ_CONFIG["project"]
        )
        assert sorted(out_df["A"].tolist()) == ["1", "1", "1"]

        materialize(
            [self_dependent_asset],
            partition_key="2023-01-02",
            resources=resource_defs,
            run_config={
                "ops": {
                    asset_full_name: {"config": {"value": "2", "last_partition_key": "2023-01-01"}}
                }
            },
        )

        out_df = pandas_gbq.read_gbq(
            f"SELECT * FROM {bq_table_path}", project_id=SHARED_BUILDKITE_BQ_CONFIG["project"]
        )
        assert sorted(out_df["A"].tolist()) == ["1", "1", "1", "2", "2", "2"]
