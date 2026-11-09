import os
from unittest.mock import MagicMock

import duckdb
import polars as pl
import pytest
from dagster import (
    AssetExecutionContext,
    AssetIn,
    AssetKey,
    Out,
    TimeWindowPartitionMapping,
    asset,
    build_output_context,
    graph,
    instance_for_test,
    materialize,
    op,
)
from dagster._check import CheckError
from dagster._core.definitions.partitions.definition import (
    DailyPartitionsDefinition,
    DynamicPartitionsDefinition,
    MultiPartitionsDefinition,
    StaticPartitionsDefinition,
)
from dagster._core.definitions.partitions.utils import MultiPartitionKey
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.storage.db_io_manager import TablePartitionDimension, TableSlice
from dagster_duckdb_polars import DuckDBPolarsIOManager, duckdb_polars_io_manager
from dagster_duckdb_polars.duckdb_polars_type_handler import (
    DuckDBPolarsTypeHandler,
    _existing_table_columns,
)


def test_handle_output_empty_dataframe():
    handler = DuckDBPolarsTypeHandler()
    df = pl.DataFrame({"a": pl.Series([], dtype=pl.Int64), "b": pl.Series([], dtype=pl.Int64)})
    connection = MagicMock()
    output_context = build_output_context()

    handler.handle_output(
        output_context,
        TableSlice(
            table="my_table",
            schema="my_schema",
            database="my_db",
            columns=None,
            partition_dimensions=[],
        ),
        df,
        connection,
    )

    connection.execute.assert_not_called()


@pytest.fixture
def io_managers(tmp_path):
    return [
        duckdb_polars_io_manager.configured(
            {"database": os.path.join(tmp_path, "unit_test.duckdb")}
        ),
        DuckDBPolarsIOManager(database=os.path.join(tmp_path, "unit_test.duckdb")),
    ]


@op(out=Out(metadata={"schema": "a_df"}))
def a_df() -> pl.DataFrame:
    return pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})


@op(out=Out(metadata={"schema": "add_one"}))
def add_one(df: pl.DataFrame):
    return df + 1


@graph
def add_one_to_dataframe():
    add_one(a_df())


def test_duckdb_io_manager_with_ops(tmp_path, io_managers):
    for io_manager in io_managers:
        resource_defs = {"io_manager": io_manager}

        job = add_one_to_dataframe.to_job(resource_defs=resource_defs)

        # run the job twice to ensure that tables get properly deleted
        for _ in range(2):
            res = job.execute_in_process()

            assert res.success
            duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))

            out_df = pl.DataFrame(duckdb_conn.execute("SELECT * FROM a_df.result").arrow())
            assert out_df["a"].to_list() == [1, 2, 3]

            out_df = pl.DataFrame(duckdb_conn.execute("SELECT * FROM add_one.result").arrow())
            assert out_df["a"].to_list() == [2, 3, 4]

            duckdb_conn.close()


@asset(key_prefix=["my_schema"])
def b_df() -> pl.DataFrame:
    return pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})


@asset(key_prefix=["my_schema"])
def b_plus_one(b_df: pl.DataFrame):
    return b_df + 1


def test_duckdb_io_manager_with_assets(tmp_path, io_managers):
    for io_manager in io_managers:
        resource_defs = {"io_manager": io_manager}

        # materialize asset twice to ensure that tables get properly deleted
        for _ in range(2):
            res = materialize([b_df, b_plus_one], resources=resource_defs)
            assert res.success

            duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))

            out_df = pl.DataFrame(duckdb_conn.execute("SELECT * FROM my_schema.b_df").arrow())
            assert out_df["a"].to_list() == [1, 2, 3]

            out_df = pl.DataFrame(duckdb_conn.execute("SELECT * FROM my_schema.b_plus_one").arrow())
            assert out_df["a"].to_list() == [2, 3, 4]

            duckdb_conn.close()


def test_duckdb_io_manager_with_schema(tmp_path):
    @asset
    def my_df() -> pl.DataFrame:
        return pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

    @asset
    def my_df_plus_one(my_df: pl.DataFrame) -> pl.DataFrame:
        return my_df + 1

    schema_io_managers = [
        duckdb_polars_io_manager.configured(
            {"database": os.path.join(tmp_path, "unit_test.duckdb"), "schema": "custom_schema"}
        ),
        DuckDBPolarsIOManager(
            database=os.path.join(tmp_path, "unit_test.duckdb"), schema="custom_schema"
        ),
    ]

    for io_manager in schema_io_managers:
        resource_defs = {"io_manager": io_manager}

        # materialize asset twice to ensure that tables get properly deleted
        for _ in range(2):
            res = materialize([my_df, my_df_plus_one], resources=resource_defs)
            assert res.success

            duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))

            out_df = pl.DataFrame(duckdb_conn.execute("SELECT * FROM custom_schema.my_df").arrow())
            assert out_df["a"].to_list() == [1, 2, 3]

            out_df = pl.DataFrame(
                duckdb_conn.execute("SELECT * FROM custom_schema.my_df_plus_one").arrow()
            )
            assert out_df["a"].to_list() == [2, 3, 4]

            duckdb_conn.close()


@asset(key_prefix=["my_schema"], ins={"b_df": AssetIn("b_df", metadata={"columns": ["a"]})})
def b_plus_one_columns(b_df: pl.DataFrame):
    return b_df + 1


def test_loading_columns(tmp_path, io_managers):
    for io_manager in io_managers:
        resource_defs = {"io_manager": io_manager}

        # materialize asset twice to ensure that tables get properly deleted
        for _ in range(2):
            res = materialize([b_df, b_plus_one_columns], resources=resource_defs)
            assert res.success

            duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))

            out_df = pl.DataFrame(duckdb_conn.execute("SELECT * FROM my_schema.b_df").arrow())
            assert out_df["a"].to_list() == [1, 2, 3]

            out_df = pl.DataFrame(
                duckdb_conn.execute("SELECT * FROM my_schema.b_plus_one_columns").arrow()
            )
            assert out_df["a"].to_list() == [2, 3, 4]

            assert out_df.shape[1] == 1

            duckdb_conn.close()


@op
def non_supported_type() -> int:
    return 1


@graph
def not_supported():
    non_supported_type()


def test_not_supported_type(tmp_path, io_managers):
    for io_manager in io_managers:
        resource_defs = {"io_manager": io_manager}

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
def daily_partitioned(context: AssetExecutionContext) -> pl.DataFrame:
    df = pl.DataFrame({"date": context.partition_key})
    partition = df.with_columns(
        pl.col("date").str.strptime(pl.Date, format="%Y-%m-%d", strict=False).cast(pl.Datetime)
    )["date"][0]
    value = context.op_execution_context.op_config["value"]

    return pl.DataFrame(
        {
            "time": [partition, partition, partition],
            "a": [value, value, value],
            "b": [4, 5, 6],
        }
    )


def test_time_window_partitioned_asset(tmp_path, io_managers):
    for io_manager in io_managers:
        resource_defs = {"io_manager": io_manager}

        materialize(
            [daily_partitioned],
            partition_key="2022-01-01",
            resources=resource_defs,
            run_config={"ops": {"my_schema__daily_partitioned": {"config": {"value": "1"}}}},
        )

        duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))
        out_df = pl.DataFrame(
            duckdb_conn.execute("SELECT * FROM my_schema.daily_partitioned").arrow()
        )
        assert out_df["a"].to_list() == ["1", "1", "1"]
        duckdb_conn.close()

        materialize(
            [daily_partitioned],
            partition_key="2022-01-02",
            resources=resource_defs,
            run_config={"ops": {"my_schema__daily_partitioned": {"config": {"value": "2"}}}},
        )

        duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))
        out_df = pl.DataFrame(
            duckdb_conn.execute("SELECT * FROM my_schema.daily_partitioned").arrow()
        )
        assert sorted(out_df["a"].to_list()) == ["1", "1", "1", "2", "2", "2"]
        duckdb_conn.close()

        materialize(
            [daily_partitioned],
            partition_key="2022-01-01",
            resources=resource_defs,
            run_config={"ops": {"my_schema__daily_partitioned": {"config": {"value": "3"}}}},
        )

        duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))
        out_df = pl.DataFrame(
            duckdb_conn.execute("SELECT * FROM my_schema.daily_partitioned").arrow()
        )
        assert sorted(out_df["a"].to_list()) == ["2", "2", "2", "3", "3", "3"]

        # drop table so we start with an empty db for the next io manager
        duckdb_conn.execute("DELETE FROM my_schema.daily_partitioned")
        duckdb_conn.close()


@asset(
    partitions_def=StaticPartitionsDefinition(["red", "yellow", "blue"]),
    key_prefix=["my_schema"],
    metadata={"partition_expr": "color"},
    config_schema={"value": str},
)
def static_partitioned(context: AssetExecutionContext) -> pl.DataFrame:
    partition = context.partition_key
    value = context.op_execution_context.op_config["value"]
    return pl.DataFrame(
        {
            "color": [partition, partition, partition],
            "a": [value, value, value],
            "b": [4, 5, 6],
        }
    )


def test_static_partitioned_asset(tmp_path, io_managers):
    for io_manager in io_managers:
        resource_defs = {"io_manager": io_manager}

        materialize(
            [static_partitioned],
            partition_key="red",
            resources=resource_defs,
            run_config={"ops": {"my_schema__static_partitioned": {"config": {"value": "1"}}}},
        )

        duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))
        out_df = pl.DataFrame(
            duckdb_conn.execute("SELECT * FROM my_schema.static_partitioned").arrow()
        )
        assert out_df["a"].to_list() == ["1", "1", "1"]
        duckdb_conn.close()

        materialize(
            [static_partitioned],
            partition_key="blue",
            resources=resource_defs,
            run_config={"ops": {"my_schema__static_partitioned": {"config": {"value": "2"}}}},
        )

        duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))
        out_df = pl.DataFrame(
            duckdb_conn.execute("SELECT * FROM my_schema.static_partitioned").arrow()
        )
        assert sorted(out_df["a"].to_list()) == ["1", "1", "1", "2", "2", "2"]
        duckdb_conn.close()

        materialize(
            [static_partitioned],
            partition_key="red",
            resources=resource_defs,
            run_config={"ops": {"my_schema__static_partitioned": {"config": {"value": "3"}}}},
        )

        duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))
        out_df = pl.DataFrame(
            duckdb_conn.execute("SELECT * FROM my_schema.static_partitioned").arrow()
        )
        assert sorted(out_df["a"].to_list()) == ["2", "2", "2", "3", "3", "3"]

        # drop table so we start with an empty db for the next io manager
        duckdb_conn.execute("DELETE FROM my_schema.static_partitioned")
        duckdb_conn.close()


@asset(
    partitions_def=MultiPartitionsDefinition(
        {
            "time": DailyPartitionsDefinition(start_date="2022-01-01"),
            "color": StaticPartitionsDefinition(["red", "yellow", "blue"]),
        }
    ),
    key_prefix=["my_schema"],
    metadata={"partition_expr": {"time": "CAST(time as DATE)", "color": "color"}},
    config_schema={"value": str},
)
def multi_partitioned(context) -> pl.DataFrame:
    partition = context.partition_key.keys_by_dimension
    value = context.op_execution_context.op_config["value"]
    return pl.DataFrame(
        {
            "color": [partition["color"], partition["color"], partition["color"]],
            "time": [partition["time"], partition["time"], partition["time"]],
            "a": [value, value, value],
        }
    )


def test_multi_partitioned_asset(tmp_path, io_managers):
    for io_manager in io_managers:
        resource_defs = {"io_manager": io_manager}

        materialize(
            [multi_partitioned],
            partition_key=MultiPartitionKey({"time": "2022-01-01", "color": "red"}),
            resources=resource_defs,
            run_config={"ops": {"my_schema__multi_partitioned": {"config": {"value": "1"}}}},
        )

        duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))
        out_df = pl.DataFrame(
            duckdb_conn.execute("SELECT * FROM my_schema.multi_partitioned").arrow()
        )
        assert out_df["a"].to_list() == ["1", "1", "1"]
        duckdb_conn.close()

        materialize(
            [multi_partitioned],
            partition_key=MultiPartitionKey({"time": "2022-01-01", "color": "blue"}),
            resources=resource_defs,
            run_config={"ops": {"my_schema__multi_partitioned": {"config": {"value": "2"}}}},
        )

        duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))
        out_df = pl.DataFrame(
            duckdb_conn.execute("SELECT * FROM my_schema.multi_partitioned").arrow()
        )
        assert sorted(out_df["a"].to_list()) == ["1", "1", "1", "2", "2", "2"]
        duckdb_conn.close()

        materialize(
            [multi_partitioned],
            partition_key=MultiPartitionKey({"time": "2022-01-02", "color": "red"}),
            resources=resource_defs,
            run_config={"ops": {"my_schema__multi_partitioned": {"config": {"value": "3"}}}},
        )

        duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))
        out_df = pl.DataFrame(
            duckdb_conn.execute("SELECT * FROM my_schema.multi_partitioned").arrow()
        )
        assert sorted(out_df["a"].to_list()) == ["1", "1", "1", "2", "2", "2", "3", "3", "3"]
        duckdb_conn.close()

        materialize(
            [multi_partitioned],
            partition_key=MultiPartitionKey({"time": "2022-01-01", "color": "red"}),
            resources=resource_defs,
            run_config={"ops": {"my_schema__multi_partitioned": {"config": {"value": "4"}}}},
        )

        duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))
        out_df = pl.DataFrame(
            duckdb_conn.execute("SELECT * FROM my_schema.multi_partitioned").arrow()
        )
        assert sorted(out_df["a"].to_list()) == ["2", "2", "2", "3", "3", "3", "4", "4", "4"]

        # drop table so we start with an empty db for the next io manager
        duckdb_conn.execute("DELETE FROM my_schema.multi_partitioned")
        duckdb_conn.close()


dynamic_fruits = DynamicPartitionsDefinition(name="dynamic_fruits")


@asset(
    partitions_def=dynamic_fruits,
    key_prefix=["my_schema"],
    metadata={"partition_expr": "fruit"},
    config_schema={"value": str},
)
def dynamic_partitioned(context: AssetExecutionContext) -> pl.DataFrame:
    partition = context.partition_key
    value = context.op_execution_context.op_config["value"]
    return pl.DataFrame(
        {
            "fruit": [partition, partition, partition],
            "a": [value, value, value],
        }
    )


def test_dynamic_partition(tmp_path, io_managers):
    for io_manager in io_managers:
        with instance_for_test() as instance:
            resource_defs = {"io_manager": io_manager}

            instance.add_dynamic_partitions(dynamic_fruits.name, ["apple"])  # ty: ignore[invalid-argument-type]

            materialize(
                [dynamic_partitioned],
                partition_key="apple",
                resources=resource_defs,
                instance=instance,
                run_config={"ops": {"my_schema__dynamic_partitioned": {"config": {"value": "1"}}}},
            )

            duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))
            out_df = pl.DataFrame(
                duckdb_conn.execute("SELECT * FROM my_schema.dynamic_partitioned").arrow()
            )
            assert out_df["a"].to_list() == ["1", "1", "1"]
            duckdb_conn.close()

            instance.add_dynamic_partitions(dynamic_fruits.name, ["orange"])  # ty: ignore[invalid-argument-type]

            materialize(
                [dynamic_partitioned],
                partition_key="orange",
                resources=resource_defs,
                instance=instance,
                run_config={"ops": {"my_schema__dynamic_partitioned": {"config": {"value": "2"}}}},
            )

            duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))
            out_df = pl.DataFrame(
                duckdb_conn.execute("SELECT * FROM my_schema.dynamic_partitioned").arrow()
            )
            assert sorted(out_df["a"].to_list()) == ["1", "1", "1", "2", "2", "2"]
            duckdb_conn.close()

            materialize(
                [dynamic_partitioned],
                partition_key="apple",
                resources=resource_defs,
                instance=instance,
                run_config={"ops": {"my_schema__dynamic_partitioned": {"config": {"value": "3"}}}},
            )

            duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))
            out_df = pl.DataFrame(
                duckdb_conn.execute("SELECT * FROM my_schema.dynamic_partitioned").arrow()
            )
            assert sorted(out_df["a"].to_list()) == ["2", "2", "2", "3", "3", "3"]

            # drop table so we start with an empty db for the next io manager
            duckdb_conn.execute("DELETE FROM my_schema.dynamic_partitioned")
            duckdb_conn.close()


def test_self_dependent_asset(tmp_path, io_managers):
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
            "partition_expr": "strptime(key, '%Y-%m-%d')",
        },
        config_schema={"value": str, "last_partition_key": str},
    )
    def self_dependent_asset(
        context: AssetExecutionContext, self_dependent_asset: pl.DataFrame
    ) -> pl.DataFrame:
        key = context.partition_key

        if not self_dependent_asset.is_empty():
            assert len(self_dependent_asset["key"]) == 3
            assert (
                self_dependent_asset["key"]
                == context.op_execution_context.op_config["last_partition_key"]
            ).all()
        else:
            assert context.op_execution_context.op_config["last_partition_key"] == "NA"
        value = context.op_execution_context.op_config["value"]
        pd_df = pl.DataFrame(
            {
                "key": [key, key, key],
                "a": [value, value, value],
            }
        )

        return pd_df

    for io_manager in io_managers:
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

        duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))
        out_df = pl.DataFrame(
            duckdb_conn.execute("SELECT * FROM my_schema.self_dependent_asset").arrow()
        )

        assert out_df["a"].to_list() == ["1", "1", "1"]
        duckdb_conn.close()

        materialize(
            [self_dependent_asset],
            partition_key="2023-01-02",
            resources=resource_defs,
            run_config={
                "ops": {
                    "my_schema__self_dependent_asset": {
                        "config": {"value": "2", "last_partition_key": "2023-01-01"}
                    }
                }
            },
        )

        duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))
        out_df = pl.DataFrame(
            duckdb_conn.execute("SELECT * FROM my_schema.self_dependent_asset").arrow()
        )

        assert out_df["a"].to_list() == ["1", "1", "1", "2", "2", "2"]

        # drop table so we start with an empty db for the next io manager
        duckdb_conn.execute("DELETE FROM my_schema.self_dependent_asset")
        duckdb_conn.close()


# ---------------------------------------------------------------------------
# Opt-in recreate-on-schema-mismatch tests (#17058)
# ---------------------------------------------------------------------------


def _read_schema_table(db_path, table):
    # Match DuckDbClient.connect config so readback still works after a failed
    # write leaked its connection in this process.
    conn = duckdb.connect(database=db_path, config={"custom_user_agent": "dagster"})
    try:
        return pl.DataFrame(conn.execute(f"SELECT * FROM {table} ORDER BY ALL").arrow())
    finally:
        conn.close()


def _recreate_manager(tmp_path):
    return DuckDBPolarsIOManager(
        database=os.path.join(tmp_path, "schema_test.duckdb"),
        recreate_table_on_schema_mismatch=True,
    )


def _evolving_asset(state):
    @asset(key_prefix=["my_schema"])
    def evolving_table() -> pl.DataFrame:
        return state["df"]

    return evolving_table


def _materialize_twice(tmp_path, state, first, second, io_manager=None):
    manager = io_manager or _recreate_manager(tmp_path)
    evolving_table = _evolving_asset(state)
    state["df"] = first
    assert materialize([evolving_table], resources={"io_manager": manager}).success
    state["df"] = second
    return materialize([evolving_table], resources={"io_manager": manager}).success


def test_schema_mismatch_recreate_renamed_column(tmp_path):
    state = {}
    assert _materialize_twice(
        tmp_path,
        state,
        pl.DataFrame({"a": [1, 2], "b": [3, 4]}),
        pl.DataFrame({"a": [1, 2], "c": [3, 4]}),
    )
    out = _read_schema_table(
        os.path.join(tmp_path, "schema_test.duckdb"), "my_schema.evolving_table"
    )
    assert out.columns == ["a", "c"]
    assert out["c"].to_list() == [3, 4]


def test_schema_mismatch_recreate_added_column(tmp_path):
    state = {}
    assert _materialize_twice(
        tmp_path,
        state,
        pl.DataFrame({"a": [1, 2], "b": [3, 4]}),
        pl.DataFrame({"a": [1, 2], "b": [3, 4], "c": [5, 6]}),
    )
    out = _read_schema_table(
        os.path.join(tmp_path, "schema_test.duckdb"), "my_schema.evolving_table"
    )
    assert out.columns == ["a", "b", "c"]
    assert out["c"].to_list() == [5, 6]


def test_schema_mismatch_recreate_dropped_column(tmp_path):
    state = {}
    assert _materialize_twice(
        tmp_path,
        state,
        pl.DataFrame({"a": [1, 2], "b": [3, 4]}),
        pl.DataFrame({"a": [1, 2]}),
    )
    out = _read_schema_table(
        os.path.join(tmp_path, "schema_test.duckdb"), "my_schema.evolving_table"
    )
    assert out.columns == ["a"]
    assert out["a"].to_list() == [1, 2]


def test_schema_mismatch_recreate_reordered_same_type(tmp_path):
    state = {}
    assert _materialize_twice(
        tmp_path,
        state,
        pl.DataFrame({"a": [1, 2], "b": [10, 20]}),
        pl.DataFrame({"b": [10, 20], "a": [1, 2]}),
    )
    out = _read_schema_table(
        os.path.join(tmp_path, "schema_test.duckdb"), "my_schema.evolving_table"
    )
    assert out.columns == ["b", "a"]
    assert out["a"].to_list() == [1, 2]
    assert out["b"].to_list() == [10, 20]


def test_schema_mismatch_dtype_only_keeps_existing_behavior(tmp_path):
    # Names match, so recreate must not trigger: an incompatible dtype still
    # fails on insert (cast-or-error), even with opt-in enabled.
    state = {}
    manager = _recreate_manager(tmp_path)
    evolving_table = _evolving_asset(state)
    state["df"] = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
    assert materialize([evolving_table], resources={"io_manager": manager}).success
    state["df"] = pl.DataFrame({"a": ["x", "y"], "b": [3, 4]})
    result = materialize([evolving_table], resources={"io_manager": manager}, raise_on_error=False)
    assert not result.success
    out = _read_schema_table(
        os.path.join(tmp_path, "schema_test.duckdb"), "my_schema.evolving_table"
    )
    assert out.columns == ["a", "b"]


def test_schema_mismatch_empty_dataframe_leaves_schema_unchanged(tmp_path):
    state = {}
    manager = _recreate_manager(tmp_path)
    evolving_table = _evolving_asset(state)
    state["df"] = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
    assert materialize([evolving_table], resources={"io_manager": manager}).success
    state["df"] = pl.DataFrame({"x": pl.Series([], dtype=pl.Int64)})
    assert materialize([evolving_table], resources={"io_manager": manager}).success
    out = _read_schema_table(
        os.path.join(tmp_path, "schema_test.duckdb"), "my_schema.evolving_table"
    )
    assert out.columns == ["a", "b"]


def test_schema_mismatch_unchanged_schema_overwrites(tmp_path):
    state = {}
    assert _materialize_twice(
        tmp_path,
        state,
        pl.DataFrame({"a": [1, 2], "b": [3, 4]}),
        pl.DataFrame({"a": [5, 6], "b": [7, 8]}),
    )
    out = _read_schema_table(
        os.path.join(tmp_path, "schema_test.duckdb"), "my_schema.evolving_table"
    )
    assert out.columns == ["a", "b"]
    assert out["a"].to_list() == [5, 6]


def test_schema_mismatch_default_off_keeps_legacy_failure(tmp_path):
    state = {}
    manager = DuckDBPolarsIOManager(database=os.path.join(tmp_path, "schema_test.duckdb"))
    evolving_table = _evolving_asset(state)
    state["df"] = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
    assert materialize([evolving_table], resources={"io_manager": manager}).success
    state["df"] = pl.DataFrame({"a": [1, 2], "b": [3, 4], "c": [5, 6]})
    result = materialize([evolving_table], resources={"io_manager": manager}, raise_on_error=False)
    assert not result.success
    out = _read_schema_table(
        os.path.join(tmp_path, "schema_test.duckdb"), "my_schema.evolving_table"
    )
    assert out.columns == ["a", "b"]


def test_schema_mismatch_recreate_op_output(tmp_path):
    state = {"df": pl.DataFrame({"a": [1, 2], "b": [3, 4]})}

    @op(out=Out(metadata={"schema": "evolving_op"}))
    def evolving_op() -> pl.DataFrame:
        return state["df"]

    @graph
    def evolving_graph():
        evolving_op()

    job = evolving_graph.to_job(resource_defs={"io_manager": _recreate_manager(tmp_path)})
    assert job.execute_in_process().success
    state["df"] = pl.DataFrame({"a": [1, 2], "b": [3, 4], "c": [5, 6]})
    assert job.execute_in_process().success
    out = _read_schema_table(os.path.join(tmp_path, "schema_test.duckdb"), "evolving_op.result")
    assert out.columns == ["a", "b", "c"]
    assert out["c"].to_list() == [5, 6]


def test_schema_mismatch_partitioned_refuses_and_preserves_other_partitions(tmp_path):
    state = {"extra": False}

    @asset(
        key_prefix=["my_schema"],
        partitions_def=StaticPartitionsDefinition(["red", "blue"]),
        metadata={"partition_expr": "color"},
    )
    def evolving_partitioned_table(context) -> pl.DataFrame:
        data = {"color": [context.partition_key], "a": [1]}
        if state["extra"]:
            data["c"] = [99]
        return pl.DataFrame(data)

    manager = _recreate_manager(tmp_path)
    assert materialize(
        [evolving_partitioned_table],
        partition_key="red",
        resources={"io_manager": manager},
    ).success
    state["extra"] = True
    result = materialize(
        [evolving_partitioned_table],
        partition_key="blue",
        resources={"io_manager": manager},
        raise_on_error=False,
    )
    assert not result.success
    out = _read_schema_table(
        os.path.join(tmp_path, "schema_test.duckdb"), "my_schema.evolving_partitioned_table"
    )
    assert sorted(out["color"].to_list()) == ["red"]


def test_schema_mismatch_multi_partitioned_refuses_and_preserves_other_partitions(tmp_path):
    state = {"extra": False}

    @asset(
        key_prefix=["my_schema"],
        partitions_def=MultiPartitionsDefinition(
            {
                "time": DailyPartitionsDefinition(start_date="2022-01-01"),
                "color": StaticPartitionsDefinition(["red", "blue"]),
            }
        ),
        metadata={"partition_expr": {"time": "CAST(time as DATE)", "color": "color"}},
    )
    def evolving_multi_partitioned_table(context) -> pl.DataFrame:
        keys = context.partition_key.keys_by_dimension
        data = {
            "color": [keys["color"]],
            "time": [keys["time"]],
            "a": [1],
        }
        if state["extra"]:
            data["c"] = [99]
        return pl.DataFrame(data)

    manager = _recreate_manager(tmp_path)
    assert materialize(
        [evolving_multi_partitioned_table],
        partition_key=MultiPartitionKey({"time": "2022-01-01", "color": "red"}),
        resources={"io_manager": manager},
    ).success
    state["extra"] = True
    result = materialize(
        [evolving_multi_partitioned_table],
        partition_key=MultiPartitionKey({"time": "2022-01-01", "color": "blue"}),
        resources={"io_manager": manager},
        raise_on_error=False,
    )
    assert not result.success
    out = _read_schema_table(
        os.path.join(tmp_path, "schema_test.duckdb"),
        "my_schema.evolving_multi_partitioned_table",
    )
    assert sorted(out["color"].to_list()) == ["red"]


def test_schema_mismatch_partitioned_handler_error_message(tmp_path):
    db_path = os.path.join(tmp_path, "schema_handler.duckdb")
    conn = duckdb.connect(database=db_path, config={"custom_user_agent": "dagster"})
    conn.execute("create schema if not exists my_schema;")
    conn.execute("create table my_schema.slice_table (color VARCHAR, a BIGINT);")
    conn.execute("insert into my_schema.slice_table values ('red', 1);")
    handler = DuckDBPolarsTypeHandler(recreate_table_on_schema_mismatch=True)
    with pytest.raises(DagsterInvariantViolationError, match="partitioned"):
        handler.handle_output(
            build_output_context(),
            TableSlice(
                table="slice_table",
                schema="my_schema",
                database=db_path,
                columns=None,
                partition_dimensions=[
                    TablePartitionDimension(partition_expr="color", partitions=["blue"])
                ],
            ),
            pl.DataFrame({"color": ["blue"], "a": [1], "c": [99]}),
            conn,
        )
    rows = conn.execute("SELECT color FROM my_schema.slice_table").fetchall()
    assert rows == [("red",)]
    conn.close()


def test_schema_mismatch_respects_subclass_type_handlers(tmp_path):
    class CustomHandler(DuckDBPolarsTypeHandler):
        pass

    class CustomManager(DuckDBPolarsIOManager):
        @staticmethod
        def type_handlers():
            return [CustomHandler()]

    for flag in (False, True):
        manager = CustomManager(
            database=os.path.join(tmp_path, "subclass.duckdb"),
            recreate_table_on_schema_mismatch=flag,
        )
        handlers = list(manager.create_io_manager(None)._handlers_by_type.values())  # noqa: SLF001
        assert [type(h) for h in handlers] == [CustomHandler]

    stock = _recreate_manager(tmp_path).create_io_manager(None)
    stock_handlers = list(stock._handlers_by_type.values())  # noqa: SLF001
    assert [type(h) for h in stock_handlers] == [DuckDBPolarsTypeHandler]
    assert stock_handlers[0]._recreate_table_on_schema_mismatch  # noqa: SLF001


def test_schema_mismatch_quoted_schema_repeated_write(tmp_path):
    state = {}
    db_path = os.path.join(tmp_path, "schema_test.duckdb")
    manager = DuckDBPolarsIOManager(
        database=db_path,
        schema='"custom-schema"',
        recreate_table_on_schema_mismatch=True,
    )
    evolving_table = _evolving_asset(state)
    state["df"] = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
    assert materialize([evolving_table], resources={"io_manager": manager}).success
    state["df"] = pl.DataFrame({"a": [5, 6], "b": [7, 8]})
    assert materialize([evolving_table], resources={"io_manager": manager}).success
    out = _read_schema_table(db_path, '"custom-schema".evolving_table')
    assert out.columns == ["a", "b"]
    assert out["a"].to_list() == [5, 6]
    state["df"] = pl.DataFrame({"a": [9], "b": [10], "c": [11]})
    assert materialize([evolving_table], resources={"io_manager": manager}).success
    out = _read_schema_table(db_path, '"custom-schema".evolving_table')
    assert out.columns == ["a", "b", "c"]
    assert out["c"].to_list() == [11]


def test_existing_table_columns_quoted_identifiers(tmp_path):
    db_path = os.path.join(tmp_path, "quoted.duckdb")
    conn = duckdb.connect(database=db_path, config={"custom_user_agent": "dagster"})
    conn.execute('create schema "my-schema";')
    conn.execute('create table "my-schema"."my-table" (a BIGINT, b VARCHAR);')
    conn.execute('create schema "weird""schema";')
    conn.execute('create table "weird""schema".t1 (x BIGINT);')
    assert _existing_table_columns(
        conn,
        TableSlice(
            table='"my-table"',
            schema='"my-schema"',
            database=db_path,
            columns=None,
            partition_dimensions=[],
        ),
    ) == ["a", "b"]
    assert _existing_table_columns(
        conn,
        TableSlice(
            table="t1",
            schema='"weird""schema"',
            database=db_path,
            columns=None,
            partition_dimensions=[],
        ),
    ) == ["x"]
    assert (
        _existing_table_columns(
            conn,
            TableSlice(
                table='"missing-table"',
                schema='"my-schema"',
                database=db_path,
                columns=None,
                partition_dimensions=[],
            ),
        )
        is None
    )
    conn.close()


def test_schema_mismatch_legacy_subclass_without_super_init(tmp_path):
    class LegacyHandler(DuckDBPolarsTypeHandler):
        def __init__(self):
            pass

    assert LegacyHandler()._recreate_table_on_schema_mismatch is False  # noqa: SLF001
    db_path = os.path.join(tmp_path, "legacy.duckdb")
    conn = duckdb.connect(database=db_path, config={"custom_user_agent": "dagster"})
    LegacyHandler().handle_output(
        build_output_context(),
        TableSlice(
            table="legacy_table",
            schema="my_schema",
            database=db_path,
            columns=None,
            partition_dimensions=[],
        ),
        pl.DataFrame({"a": [1]}),
        conn,
    )
    rows = conn.execute("SELECT a FROM my_schema.legacy_table").fetchall()
    assert rows == [(1,)]
    conn.close()
