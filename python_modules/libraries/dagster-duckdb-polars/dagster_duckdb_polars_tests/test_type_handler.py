import os

import duckdb
import polars as pl
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
from dagster_duckdb_polars import DuckDBPolarsIOManager, duckdb_polars_io_manager


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

            instance.add_dynamic_partitions(dynamic_fruits.name, ["apple"])  # pyright: ignore[reportArgumentType]

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

            instance.add_dynamic_partitions(dynamic_fruits.name, ["orange"])  # pyright: ignore[reportArgumentType]

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
