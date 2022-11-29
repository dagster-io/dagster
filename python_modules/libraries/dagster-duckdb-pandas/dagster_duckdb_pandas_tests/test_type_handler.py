import os

import duckdb
import pandas as pd
import pytest
from dagster_duckdb_pandas import duckdb_pandas_io_manager

from dagster import AssetIn, DailyPartitionsDefinition, Out, asset, graph, materialize, op
from dagster._check import CheckError


@op(out=Out(metadata={"schema": "a_df"}))
def a_df() -> pd.DataFrame:
    return pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})


@op(out=Out(metadata={"schema": "add_one"}))
def add_one(df: pd.DataFrame):
    return df + 1


@graph
def add_one_to_dataframe():
    add_one(a_df())


def test_duckdb_io_manager_with_ops(tmp_path):
    resource_defs = {
        "io_manager": duckdb_pandas_io_manager.configured(
            {"database": os.path.join(tmp_path, "unit_test.duckdb")}
        ),
    }

    job = add_one_to_dataframe.to_job(resource_defs=resource_defs)

    # run the job twice to ensure that tables get properly deleted
    for _ in range(2):
        res = job.execute_in_process()

        assert res.success
        duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))

        out_df = duckdb_conn.execute("SELECT * FROM a_df.result").fetch_df()
        assert out_df["a"].tolist() == [1, 2, 3]

        out_df = duckdb_conn.execute("SELECT * FROM add_one.result").fetch_df()
        assert out_df["a"].tolist() == [2, 3, 4]

        duckdb_conn.close()


@asset(key_prefix=["my_schema"])
def b_df() -> pd.DataFrame:
    return pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})


@asset(key_prefix=["my_schema"])
def b_plus_one(b_df: pd.DataFrame):
    return b_df + 1


def test_duckdb_io_manager_with_assets(tmp_path):
    resource_defs = {
        "io_manager": duckdb_pandas_io_manager.configured(
            {"database": os.path.join(tmp_path, "unit_test.duckdb")}
        ),
    }

    # materialize asset twice to ensure that tables get properly deleted
    for _ in range(2):
        res = materialize([b_df, b_plus_one], resources=resource_defs)
        assert res.success

        duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))

        out_df = duckdb_conn.execute("SELECT * FROM my_schema.b_df").fetch_df()
        assert out_df["a"].tolist() == [1, 2, 3]

        out_df = duckdb_conn.execute("SELECT * FROM my_schema.b_plus_one").fetch_df()
        assert out_df["a"].tolist() == [2, 3, 4]

        duckdb_conn.close()


@asset(key_prefix=["my_schema"], ins={"b_df": AssetIn("b_df", metadata={"columns": ["a"]})})
def b_plus_one_columns(b_df: pd.DataFrame):
    return b_df + 1


def test_loading_columns(tmp_path):
    resource_defs = {
        "io_manager": duckdb_pandas_io_manager.configured(
            {"database": os.path.join(tmp_path, "unit_test.duckdb")}
        ),
    }

    # materialize asset twice to ensure that tables get properly deleted
    for _ in range(2):
        res = materialize([b_df, b_plus_one_columns], resources=resource_defs)
        assert res.success

        duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))

        out_df = duckdb_conn.execute("SELECT * FROM my_schema.b_df").fetch_df()
        assert out_df["a"].tolist() == [1, 2, 3]

        out_df = duckdb_conn.execute("SELECT * FROM my_schema.b_plus_one_columns").fetch_df()
        assert out_df["a"].tolist() == [2, 3, 4]

        assert out_df.shape[1] == 1

        duckdb_conn.close()


@op
def non_supported_type() -> int:
    return 1


@graph
def not_supported():
    non_supported_type()


def test_not_supported_type(tmp_path):
    resource_defs = {
        "io_manager": duckdb_pandas_io_manager.configured(
            {"database": os.path.join(tmp_path, "unit_test.duckdb")}
        ),
    }

    job = not_supported.to_job(resource_defs=resource_defs)

    with pytest.raises(
        CheckError,
        match="DuckDBIOManager does not have a handler for type '<class 'int'>'",
    ):
        job.execute_in_process()


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2022-01-01"),
    key_prefix=["my_schema"],
    metadata={"partition_expr": "time"},
    config_schema={"value": str},
)
def daily_partitioned(context):
    partition = pd.Timestamp(context.asset_partition_key_for_output())
    value = context.op_config["value"]

    return pd.DataFrame(
        {
            "time": [partition, partition, partition],
            "a": [value, value, value],
            "b": [4, 5, 6],
        }
    )


def test_partitioned_asset(tmp_path):
    duckdb_io_manager = duckdb_pandas_io_manager.configured(
        {"database": os.path.join(tmp_path, "unit_test.duckdb")}
    )
    resource_defs = {"io_manager": duckdb_io_manager}

    materialize(
        [daily_partitioned],
        partition_key="2022-01-01",
        resources=resource_defs,
        run_config={"ops": {"my_schema__daily_partitioned": {"config": {"value": "1"}}}},
    )

    duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))
    out_df = duckdb_conn.execute("SELECT * FROM my_schema.daily_partitioned").fetch_df()
    assert out_df["a"].tolist() == ["1", "1", "1"]
    duckdb_conn.close()

    materialize(
        [daily_partitioned],
        partition_key="2022-01-02",
        resources=resource_defs,
        run_config={"ops": {"my_schema__daily_partitioned": {"config": {"value": "2"}}}},
    )

    duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))
    out_df = duckdb_conn.execute("SELECT * FROM my_schema.daily_partitioned").fetch_df()
    assert sorted(out_df["a"].tolist()) == ["1", "1", "1", "2", "2", "2"]
    duckdb_conn.close()

    materialize(
        [daily_partitioned],
        partition_key="2022-01-01",
        resources=resource_defs,
        run_config={"ops": {"my_schema__daily_partitioned": {"config": {"value": "3"}}}},
    )

    duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))
    out_df = duckdb_conn.execute("SELECT * FROM my_schema.daily_partitioned").fetch_df()
    assert sorted(out_df["a"].tolist()) == ["2", "2", "2", "3", "3", "3"]
    duckdb_conn.close()
