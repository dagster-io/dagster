import os

import pyarrow as pa
import pytest
from dagster import (
    Out,
    graph,
    op,
)
from dagster_deltalake import DeltaLakePyarrowIOManager, LocalConfig, WriterEngine
from deltalake import DeltaTable


@pytest.fixture
def io_manager(tmp_path) -> DeltaLakePyarrowIOManager:
    return DeltaLakePyarrowIOManager(
        root_uri=str(tmp_path), storage_options=LocalConfig(), writer_engine=WriterEngine.rust
    )


@op(
    out=Out(
        metadata={"schema": "a_df", "mode": "append", "custom_metadata": {"userName": "John Doe"}}
    )
)
def a_df() -> pa.Table:
    return pa.Table.from_pydict({"a": [1, 2, 3], "b": [4, 5, 6]})


@graph
def to_one_df():
    a_df()


def test_deltalake_io_manager_with_ops_rust_writer(tmp_path, io_manager):
    resource_defs = {"io_manager": io_manager}

    job = to_one_df.to_job(resource_defs=resource_defs)

    result = [1, 2, 3]
    for _ in range(1, 4):
        res = job.execute_in_process()

        assert res.success

        dt = DeltaTable(os.path.join(tmp_path, "a_df/result"))
        last_action = dt.history(1)[0]
        assert last_action["userName"] == "John Doe"
        out_df = dt.to_pyarrow_table()
        assert out_df["a"].to_pylist() == result

        result.extend([1, 2, 3])


@pytest.fixture
def io_manager_with_writer_metadata(tmp_path) -> DeltaLakePyarrowIOManager:
    return DeltaLakePyarrowIOManager(
        root_uri=str(tmp_path),
        storage_options=LocalConfig(),
        writer_engine=WriterEngine.rust,
        custom_metadata={"userName": "John Doe"},
        writer_properties={"compression": "ZSTD"},
    )


@op(out=Out(metadata={"schema": "a_df"}))
def a_df2() -> pa.Table:
    return pa.Table.from_pydict({"a": [1, 2, 3], "b": [4, 5, 6]})


@graph
def to_one_df2():
    a_df2()


def test_deltalake_io_manager_with_additional_configs(tmp_path, io_manager_with_writer_metadata):
    resource_defs = {"io_manager": io_manager_with_writer_metadata}

    job = to_one_df2.to_job(resource_defs=resource_defs)
    res = job.execute_in_process()

    assert res.success

    dt = DeltaTable(os.path.join(tmp_path, "a_df/result"))

    last_action = dt.history(1)[0]
    assert last_action["userName"] == "John Doe"

    file = dt.get_add_actions()["path"].to_pylist()[0]
    assert os.path.splitext(os.path.splitext(file)[0])[1] == ".zstd"

    out_df = dt.to_pyarrow_table()
    assert out_df["a"].to_pylist() == [1, 2, 3]
