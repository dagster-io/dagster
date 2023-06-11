import os

import pyarrow as pa
import pytest
from dagster import Out, asset, graph, materialize, op
from dagster_deltalake import DeltaTablePyarrowIOManager, LocalConfig
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
