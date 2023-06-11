import os
from datetime import datetime

import pyarrow as pa
import pytest
from dagster import AssetIn, DailyPartitionsDefinition, Out, asset, graph, materialize, op
from dagster._check import CheckError
from dagster_deltalake import DELTA_DATE_FORMAT, DeltaTablePyarrowIOManager, LocalConfig
from deltalake import DeltaTable


@pytest.fixture
def io_manager(tmp_path) -> DeltaTablePyarrowIOManager:
    return DeltaTablePyarrowIOManager(root_uri=str(tmp_path), storage_options=LocalConfig())


@op(out=Out(metadata={"schema": "a_df"}))
def a_df() -> pa.Table:
    return pa.Table.from_pydict({"a": [1, 2, 3], "b": [4, 5, 6]})


@op(out=Out(metadata={"schema": "add_one"}))
def add_one(df: pa.Table):
    return df.set_column(0, "a", pa.array([2, 3, 4]))


@graph
def add_one_to_dataframe():
    add_one(a_df())


def test_deltalake_io_manager_with_ops(tmp_path, io_manager: DeltaTablePyarrowIOManager):
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


def test_deltalake_io_manager_with_assets(tmp_path, io_manager: DeltaTablePyarrowIOManager):
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

    io_manager = DeltaTablePyarrowIOManager(
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
def daily_partitioned(context) -> pa.Table:
    partition = datetime.strptime(
        context.asset_partition_key_for_output(), DELTA_DATE_FORMAT
    ).date()
    value = context.op_config["value"]

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
