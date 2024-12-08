import os
from datetime import datetime

import pyarrow as pa
import pytest
from dagster import (
    AssetExecutionContext,
    AssetIn,
    AssetKey,
    DailyPartitionsDefinition,
    DynamicPartitionsDefinition,
    MultiPartitionKey,
    MultiPartitionsDefinition,
    Out,
    StaticPartitionsDefinition,
    TimeWindowPartitionMapping,
    asset,
    graph,
    instance_for_test,
    materialize,
    op,
)
from dagster._check import CheckError
from dagster_deltalake import DELTA_DATE_FORMAT, DeltaLakePyarrowIOManager, LocalConfig
from deltalake import DeltaTable


@pytest.fixture
def io_manager(tmp_path) -> DeltaLakePyarrowIOManager:
    return DeltaLakePyarrowIOManager(root_uri=str(tmp_path), storage_options=LocalConfig())


@op(out=Out(metadata={"schema": "a_df"}))
def a_df() -> pa.Table:
    return pa.Table.from_pydict({"a": [1, 2, 3], "b": [4, 5, 6]})


@op(out=Out(metadata={"schema": "add_one"}))
def add_one(df: pa.Table):
    return df.set_column(0, "a", pa.array([2, 3, 4]))


@graph
def add_one_to_dataframe():
    add_one(a_df())


def test_deltalake_io_manager_with_ops(tmp_path, io_manager):
    resource_defs = {"io_manager": io_manager}

    job = add_one_to_dataframe.to_job(resource_defs=resource_defs)

    # run the job twice to ensure that tables get properly deleted
    for _ in range(2):
        res = job.execute_in_process()

        assert res.success

        dt = DeltaTable(os.path.join(tmp_path, "a_df/result"))
        out_df = dt.to_pyarrow_table()
        assert out_df["a"].to_pylist() == [1, 2, 3]

        dt = DeltaTable(os.path.join(tmp_path, "add_one/result"))
        out_df = dt.to_pyarrow_table()
        assert out_df["a"].to_pylist() == [2, 3, 4]


@asset(key_prefix=["my_schema"])
def b_df() -> pa.Table:
    return pa.Table.from_pydict({"a": [1, 2, 3], "b": [4, 5, 6]})


@asset(key_prefix=["my_schema"])
def b_plus_one(b_df: pa.Table) -> pa.Table:
    return b_df.set_column(0, "a", pa.array([2, 3, 4]))


def test_deltalake_io_manager_with_assets(tmp_path, io_manager):
    resource_defs = {"io_manager": io_manager}

    # materialize asset twice to ensure that tables get properly deleted
    for _ in range(2):
        res = materialize([b_df, b_plus_one], resources=resource_defs)
        assert res.success

        dt = DeltaTable(os.path.join(tmp_path, "my_schema/b_df"))
        out_df = dt.to_pyarrow_table()
        assert out_df["a"].to_pylist() == [1, 2, 3]

        dt = DeltaTable(os.path.join(tmp_path, "my_schema/b_plus_one"))
        out_df = dt.to_pyarrow_table()
        assert out_df["a"].to_pylist() == [2, 3, 4]


def test_deltalake_io_manager_with_schema(tmp_path):
    @asset
    def my_df() -> pa.Table:
        return pa.Table.from_pydict({"a": [1, 2, 3], "b": [4, 5, 6]})

    @asset
    def my_df_plus_one(my_df: pa.Table) -> pa.Table:
        return my_df.set_column(0, "a", pa.array([2, 3, 4]))

    io_manager = DeltaLakePyarrowIOManager(
        root_uri=str(tmp_path), storage_options=LocalConfig(), schema="custom_schema"
    )

    resource_defs = {"io_manager": io_manager}

    # materialize asset twice to ensure that tables get properly deleted
    for _ in range(2):
        res = materialize([my_df, my_df_plus_one], resources=resource_defs)
        assert res.success

        dt = DeltaTable(os.path.join(tmp_path, "custom_schema/my_df"))
        out_df = dt.to_pyarrow_table()
        assert out_df["a"].to_pylist() == [1, 2, 3]

        dt = DeltaTable(os.path.join(tmp_path, "custom_schema/my_df_plus_one"))
        out_df = dt.to_pyarrow_table()
        assert out_df["a"].to_pylist() == [2, 3, 4]


@asset(key_prefix=["my_schema"], ins={"b_df": AssetIn("b_df", metadata={"columns": ["a"]})})
def b_plus_one_columns(b_df: pa.Table) -> pa.Table:
    return b_df.set_column(0, "a", pa.array([2, 3, 4]))


def test_loading_columns(tmp_path, io_manager):
    resource_defs = {"io_manager": io_manager}

    # materialize asset twice to ensure that tables get properly deleted
    for _ in range(2):
        res = materialize([b_df, b_plus_one_columns], resources=resource_defs)
        assert res.success

        dt = DeltaTable(os.path.join(tmp_path, "my_schema/b_df"))
        out_df = dt.to_pyarrow_table()
        assert out_df["a"].to_pylist() == [1, 2, 3]

        dt = DeltaTable(os.path.join(tmp_path, "my_schema/b_plus_one_columns"))
        out_df = dt.to_pyarrow_table()
        assert out_df["a"].to_pylist() == [2, 3, 4]

        assert out_df.shape[1] == 1


@op
def non_supported_type() -> int:
    return 1


@graph
def not_supported():
    non_supported_type()


def test_not_supported_type(tmp_path, io_manager):
    resource_defs = {"io_manager": io_manager}

    job = not_supported.to_job(resource_defs=resource_defs)

    with pytest.raises(
        CheckError,
        match="DeltaLakeIOManager does not have a handler for type '<class 'int'>'",
    ):
        job.execute_in_process()


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2022-01-01"),
    key_prefix=["my_schema"],
    metadata={"partition_expr": "time"},
    config_schema={"value": str},
)
def daily_partitioned(context: AssetExecutionContext) -> pa.Table:
    partition = datetime.strptime(context.partition_key, DELTA_DATE_FORMAT).date()
    value = context.op_execution_context.op_config["value"]

    return pa.Table.from_pydict(
        {
            "time": [partition, partition, partition],
            "a": [value, value, value],
            "b": [4, 5, 6],
        }
    )


def test_time_window_partitioned_asset(tmp_path, io_manager):
    resource_defs = {"io_manager": io_manager}

    materialize(
        [daily_partitioned],
        partition_key="2022-01-01",
        resources=resource_defs,
        run_config={"ops": {"my_schema__daily_partitioned": {"config": {"value": "1"}}}},
    )

    dt = DeltaTable(os.path.join(tmp_path, "my_schema/daily_partitioned"))
    out_df = dt.to_pyarrow_table()
    assert out_df["a"].to_pylist() == ["1", "1", "1"]

    materialize(
        [daily_partitioned],
        partition_key="2022-01-02",
        resources=resource_defs,
        run_config={"ops": {"my_schema__daily_partitioned": {"config": {"value": "2"}}}},
    )

    dt.update_incremental()
    out_df = dt.to_pyarrow_table()
    assert sorted(out_df["a"].to_pylist()) == ["1", "1", "1", "2", "2", "2"]

    materialize(
        [daily_partitioned],
        partition_key="2022-01-01",
        resources=resource_defs,
        run_config={"ops": {"my_schema__daily_partitioned": {"config": {"value": "3"}}}},
    )

    dt.update_incremental()
    out_df = dt.to_pyarrow_table()
    assert sorted(out_df["a"].to_pylist()) == ["2", "2", "2", "3", "3", "3"]


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2022-01-01"),
    key_prefix=["my_schema"],
    metadata={"partition_expr": "time"},
)
def load_partitioned(context, daily_partitioned: pa.Table) -> pa.Table:
    return daily_partitioned


def test_load_partitioned_asset(tmp_path, io_manager):
    resource_defs = {"io_manager": io_manager}

    res = materialize(
        [daily_partitioned, load_partitioned],
        partition_key="2022-01-01",
        resources=resource_defs,
        run_config={"ops": {"my_schema__daily_partitioned": {"config": {"value": "1"}}}},
    )

    assert res.success
    table = res.asset_value(["my_schema", "load_partitioned"])
    assert table.shape[0] == 3

    res = materialize(
        [daily_partitioned, load_partitioned],
        partition_key="2022-01-02",
        resources=resource_defs,
        run_config={"ops": {"my_schema__daily_partitioned": {"config": {"value": "2"}}}},
    )

    assert res.success
    table = res.asset_value(["my_schema", "load_partitioned"])
    assert table.shape[0] == 3


@asset(
    partitions_def=StaticPartitionsDefinition(["red", "yellow", "blue"]),
    key_prefix=["my_schema"],
    metadata={"partition_expr": "color"},
    config_schema={"value": str},
)
def static_partitioned(context: AssetExecutionContext) -> pa.Table:
    partition = context.partition_key
    value = context.op_execution_context.op_config["value"]

    return pa.Table.from_pydict(
        {
            "color": [partition, partition, partition],
            "a": [value, value, value],
            "b": [4, 5, 6],
        }
    )


def test_static_partitioned_asset(tmp_path, io_manager):
    resource_defs = {"io_manager": io_manager}

    materialize(
        [static_partitioned],
        partition_key="red",
        resources=resource_defs,
        run_config={"ops": {"my_schema__static_partitioned": {"config": {"value": "1"}}}},
    )

    dt = DeltaTable(os.path.join(tmp_path, "my_schema/static_partitioned"))
    out_df = dt.to_pyarrow_table()
    assert out_df["a"].to_pylist() == ["1", "1", "1"]

    materialize(
        [static_partitioned],
        partition_key="blue",
        resources=resource_defs,
        run_config={"ops": {"my_schema__static_partitioned": {"config": {"value": "2"}}}},
    )

    dt.update_incremental()
    out_df = dt.to_pyarrow_table()
    assert sorted(out_df["a"].to_pylist()) == ["1", "1", "1", "2", "2", "2"]

    materialize(
        [static_partitioned],
        partition_key="red",
        resources=resource_defs,
        run_config={"ops": {"my_schema__static_partitioned": {"config": {"value": "3"}}}},
    )

    dt.update_incremental()
    out_df = dt.to_pyarrow_table()
    assert sorted(out_df["a"].to_pylist()) == ["2", "2", "2", "3", "3", "3"]


@asset(
    partitions_def=StaticPartitionsDefinition(["red", "yellow", "blue"]),
    key_prefix=["my_schema"],
    metadata={"partition_expr": "color"},
)
def load_partitioned_static(context, static_partitioned: pa.Table) -> pa.Table:
    return static_partitioned


def test_load_static_partitioned_asset(tmp_path, io_manager):
    resource_defs = {"io_manager": io_manager}

    res = materialize(
        [static_partitioned, load_partitioned_static],
        partition_key="red",
        resources=resource_defs,
        run_config={"ops": {"my_schema__static_partitioned": {"config": {"value": "1"}}}},
    )

    assert res.success
    table = res.asset_value(["my_schema", "load_partitioned_static"])
    assert table.shape[0] == 3


@asset(
    partitions_def=MultiPartitionsDefinition(
        {
            "time": DailyPartitionsDefinition(start_date="2022-01-01"),
            "color": StaticPartitionsDefinition(["red", "yellow", "blue"]),
        }
    ),
    key_prefix=["my_schema"],
    metadata={"partition_expr": {"time": "time", "color": "color"}},
    config_schema={"value": str},
)
def multi_partitioned(context) -> pa.Table:
    partition = context.partition_key.keys_by_dimension
    time_partition = datetime.strptime(partition["time"], DELTA_DATE_FORMAT).date()
    value = context.op_execution_context.op_config["value"]
    return pa.Table.from_pydict(
        {
            "color": [partition["color"], partition["color"], partition["color"]],
            "time": [time_partition, time_partition, time_partition],
            "a": [value, value, value],
        }
    )


def test_multi_partitioned_asset(tmp_path, io_manager):
    resource_defs = {"io_manager": io_manager}

    materialize(
        [multi_partitioned],
        partition_key=MultiPartitionKey({"time": "2022-01-01", "color": "red"}),
        resources=resource_defs,
        run_config={"ops": {"my_schema__multi_partitioned": {"config": {"value": "1"}}}},
    )

    dt = DeltaTable(os.path.join(tmp_path, "my_schema/multi_partitioned"))
    out_df = dt.to_pyarrow_table()
    assert out_df["a"].to_pylist() == ["1", "1", "1"]

    materialize(
        [multi_partitioned],
        partition_key=MultiPartitionKey({"time": "2022-01-01", "color": "blue"}),
        resources=resource_defs,
        run_config={"ops": {"my_schema__multi_partitioned": {"config": {"value": "2"}}}},
    )

    dt.update_incremental()
    out_df = dt.to_pyarrow_table()
    assert sorted(out_df["a"].to_pylist()) == ["1", "1", "1", "2", "2", "2"]

    materialize(
        [multi_partitioned],
        partition_key=MultiPartitionKey({"time": "2022-01-02", "color": "red"}),
        resources=resource_defs,
        run_config={"ops": {"my_schema__multi_partitioned": {"config": {"value": "3"}}}},
    )

    dt.update_incremental()
    out_df = dt.to_pyarrow_table()
    assert sorted(out_df["a"].to_pylist()) == ["1", "1", "1", "2", "2", "2", "3", "3", "3"]

    materialize(
        [multi_partitioned],
        partition_key=MultiPartitionKey({"time": "2022-01-01", "color": "red"}),
        resources=resource_defs,
        run_config={"ops": {"my_schema__multi_partitioned": {"config": {"value": "4"}}}},
    )

    dt.update_incremental()
    out_df = dt.to_pyarrow_table()
    assert sorted(out_df["a"].to_pylist()) == ["2", "2", "2", "3", "3", "3", "4", "4", "4"]


dynamic_fruits = DynamicPartitionsDefinition(name="dynamic_fruits")


@asset(
    partitions_def=dynamic_fruits,
    key_prefix=["my_schema"],
    metadata={"partition_expr": "fruit"},
    config_schema={"value": str},
)
def dynamic_partitioned(context: AssetExecutionContext) -> pa.Table:
    partition = context.partition_key
    value = context.op_execution_context.op_config["value"]
    return pa.Table.from_pydict(
        {
            "fruit": [partition, partition, partition],
            "a": [value, value, value],
        }
    )


def test_dynamic_partition(tmp_path, io_manager):
    with instance_for_test() as instance:
        resource_defs = {"io_manager": io_manager}

        instance.add_dynamic_partitions(dynamic_fruits.name, ["apple"])

        materialize(
            [dynamic_partitioned],
            partition_key="apple",
            resources=resource_defs,
            instance=instance,
            run_config={"ops": {"my_schema__dynamic_partitioned": {"config": {"value": "1"}}}},
        )

        dt = DeltaTable(os.path.join(tmp_path, "my_schema/dynamic_partitioned"))
        out_df = dt.to_pyarrow_table()
        assert out_df["a"].to_pylist() == ["1", "1", "1"]

        instance.add_dynamic_partitions(dynamic_fruits.name, ["orange"])

        materialize(
            [dynamic_partitioned],
            partition_key="orange",
            resources=resource_defs,
            instance=instance,
            run_config={"ops": {"my_schema__dynamic_partitioned": {"config": {"value": "2"}}}},
        )

        dt.update_incremental()
        out_df = dt.to_pyarrow_table()
        assert sorted(out_df["a"].to_pylist()) == ["1", "1", "1", "2", "2", "2"]

        materialize(
            [dynamic_partitioned],
            partition_key="apple",
            resources=resource_defs,
            instance=instance,
            run_config={"ops": {"my_schema__dynamic_partitioned": {"config": {"value": "3"}}}},
        )

        dt.update_incremental()
        out_df = dt.to_pyarrow_table()
        assert sorted(out_df["a"].to_pylist()) == ["2", "2", "2", "3", "3", "3"]


@pytest.mark.skip("handle creating empty tables - hopw to get schema a-priory?")
def test_self_dependent_asset(tmp_path, io_manager):
    daily_partitions = DailyPartitionsDefinition(start_date="2023-01-01")

    @asset(
        partitions_def=daily_partitions,
        key_prefix=["my_schema"],
        ins={
            "self_dependent_asset": AssetIn(
                key=AssetKey(["my_schema", "self_dependent_asset"]),
                partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
            ),
        },
        metadata={
            "partition_expr": "key",
        },
        config_schema={"value": str, "last_partition_key": str},
    )
    def self_dependent_asset(
        context: AssetExecutionContext, self_dependent_asset: pa.Table
    ) -> pa.Table:
        key = datetime.strptime(context.partition_key, DELTA_DATE_FORMAT).date()

        if self_dependent_asset.num_rows > 0:
            assert self_dependent_asset.num_rows == 3
            # assert (self_dependent_asset["key"] == context.op_execution_context.op_config["last_partition_key"]).all()
        else:
            assert context.op_execution_context.op_config["last_partition_key"] == "NA"
        value = context.op_execution_context.op_config["value"]
        pd_df = pa.Table.from_pydict(
            {
                "key": [key, key, key],
                "a": [value, value, value],
            }
        )

        return pd_df

    resource_defs = {"io_manager": io_manager}

    materialize(
        [self_dependent_asset],
        partition_key="2023-01-01",
        resources=resource_defs,
        run_config={
            "ops": {
                "my_schema__self_dependent_asset": {
                    "config": {"value": "1", "last_partition_key": "NA"}
                }
            }
        },
    )

    dt = DeltaTable(os.path.join(tmp_path, "my_schema/self_dependent_asset"))
    out_df = dt.to_pyarrow_table()
    assert out_df["a"].to_pylist() == ["1", "1", "1"]
