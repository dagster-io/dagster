import os

import pyarrow as pa
import pytest
from dagster import (
    Out,
    graph,
    op,
)
from dagster_deltalake import DeltaLakePyarrowIOManager, LocalConfig, WriterEngine, WriteMode
from dagster_deltalake import MergeConfig, MergeType
from deltalake import DeltaTable


@op(out=Out(metadata={"schema": "a_df"}))
def a_df() -> pa.Table:
    return pa.Table.from_pydict({"a": [1, 2, 3], "b": [4, 5, 6]})


@op(out=Out(metadata={"schema": "add_one"}))
def add_one(df: pa.Table):
    return df.set_column(0, "a", pa.array([2, 3, 4]))


@graph
def add_one_to_dataframe():
    add_one(a_df())


@pytest.mark.parametrize("merge_type", [MergeType.deduplicate_insert, MergeType.upsert])
def test_deltalake_io_manager_with_ops_rust_writer(tmp_path, merge_type: MergeType):
    resource_defs = {
        "io_manager": DeltaLakePyarrowIOManager(
            root_uri=str(tmp_path),
            storage_options=LocalConfig(),
            mode=WriteMode.merge,
            merge_config=MergeConfig(
                merge_type=merge_type,
                predicate="s.a = t.a",
                source_alias="s",
                target_alias="t",
            ),
        )
    }

    job = add_one_to_dataframe.to_job(resource_defs=resource_defs)

    # run the job twice to ensure that tables get properly deleted
    for _ in range(2):
        res = job.execute_in_process()

        assert res.success

        dt = DeltaTable(os.path.join(tmp_path, "a_df/result"))
        out_df = dt.to_pyarrow_table()
        assert list(sorted(out_df["a"].to_pylist())) == [1, 2, 3]

        dt = DeltaTable(os.path.join(tmp_path, "add_one/result"))
        out_df = dt.to_pyarrow_table()
        assert list(sorted(out_df["a"].to_pylist())) == [2, 3, 4]
