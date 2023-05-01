import os

import duckdb
import pandas as pd
import pytest
from dagster import (
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
from dagster_duckdb_pyspark import DuckDBPySparkIOManager, duckdb_pyspark_io_manager
from pyspark.sql import (
    DataFrame as SparkDF,
    SparkSession,
)


@pytest.fixture
def io_managers(tmp_path):
    return [
        duckdb_pyspark_io_manager.configured(
            {"database": os.path.join(tmp_path, "unit_test.duckdb")}
        ),
        DuckDBPySparkIOManager(database=os.path.join(tmp_path, "unit_test.duckdb")),
    ]


@op(out=Out(metadata={"schema": "a_df"}))
def a_df() -> SparkDF:
    spark = SparkSession.builder.getOrCreate()  # type: ignore
    data = [(1, 4), (2, 5), (3, 6)]
    return spark.createDataFrame(data)


@op(out=Out(metadata={"schema": "add_one"}))
def add_one(df: SparkDF) -> SparkDF:
    return df.withColumn("_1", df._1 + 1)  # noqa: SLF001


@graph
def make_df():
    add_one(a_df())


def test_duckdb_io_manager_with_ops(tmp_path, io_managers):
    for io_manager in io_managers:
        resource_defs = {"io_manager": io_manager}

        job = make_df.to_job(resource_defs=resource_defs)

        # run the job twice to ensure that tables get properly deleted
        for _ in range(2):
            res = job.execute_in_process()

            assert res.success
            duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))

            out_df = duckdb_conn.execute("SELECT * FROM a_df.result").fetch_df()
            assert out_df["_1"].tolist() == [1, 2, 3]

            out_df = duckdb_conn.execute("SELECT * FROM add_one.result").fetch_df()
            assert out_df["_1"].tolist() == [2, 3, 4]

            duckdb_conn.close()


@asset(key_prefix=["my_schema"])
def b_df() -> SparkDF:
    spark = SparkSession.builder.getOrCreate()  # type: ignore
    data = [(1, 4), (2, 5), (3, 6)]
    return spark.createDataFrame(data)


@asset(key_prefix=["my_schema"])
def b_plus_one(b_df: SparkDF) -> SparkDF:
    return b_df.withColumn("_1", b_df._1 + 1)  # noqa: SLF001


def test_duckdb_io_manager_with_assets(tmp_path, io_managers):
    for io_manager in io_managers:
        resource_defs = {"io_manager": io_manager}

        # materialize asset twice to ensure that tables get properly deleted
        for _ in range(2):
            res = materialize([b_df, b_plus_one], resources=resource_defs)
            assert res.success

            duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))

            out_df = duckdb_conn.execute("SELECT * FROM my_schema.b_df").fetch_df()
            assert out_df["_1"].tolist() == [1, 2, 3]

            out_df = duckdb_conn.execute("SELECT * FROM my_schema.b_plus_one").fetch_df()
            assert out_df["_1"].tolist() == [2, 3, 4]

            duckdb_conn.close()


def test_duckdb_io_manager_with_schema(tmp_path):
    @asset
    def my_df() -> SparkDF:
        spark = SparkSession.builder.getOrCreate()  # type: ignore
        data = [(1, 4), (2, 5), (3, 6)]
        return spark.createDataFrame(data)

    @asset
    def my_df_plus_one(my_df: SparkDF) -> SparkDF:
        return my_df.withColumn("_1", my_df._1 + 1)  # noqa: SLF001

    schema_io_managers = [
        duckdb_pyspark_io_manager.configured(
            {"database": os.path.join(tmp_path, "unit_test.duckdb"), "schema": "custom_schema"}
        ),
        DuckDBPySparkIOManager(
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

            out_df = duckdb_conn.execute("SELECT * FROM custom_schema.my_df").fetch_df()
            assert out_df["_1"].tolist() == [1, 2, 3]

            out_df = duckdb_conn.execute("SELECT * FROM custom_schema.my_df_plus_one").fetch_df()
            assert out_df["_1"].tolist() == [2, 3, 4]

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
def daily_partitioned(context) -> SparkDF:
    partition = pd.Timestamp(context.asset_partition_key_for_output())
    value = context.op_config["value"]

    pd_df = pd.DataFrame(
        {
            "time": [partition, partition, partition],
            "a": [value, value, value],
            "b": [4, 5, 6],
        }
    )
    spark = SparkSession.builder.getOrCreate()  # type: ignore
    return spark.createDataFrame(pd_df)


def test_partitioned_asset(tmp_path, io_managers):
    for io_manager in io_managers:
        resource_defs = {"io_manager": io_manager}

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

        # drop table so we start with an empty db for the next io manager
        duckdb_conn.execute("DELETE FROM my_schema.daily_partitioned")
        duckdb_conn.close()


@asset(
    partitions_def=StaticPartitionsDefinition(["red", "yellow", "blue"]),
    key_prefix=["my_schema"],
    metadata={"partition_expr": "color"},
    config_schema={"value": str},
)
def static_partitioned(context) -> SparkDF:
    partition = context.asset_partition_key_for_output()
    value = context.op_config["value"]
    pd_df = pd.DataFrame(
        {
            "color": [partition, partition, partition],
            "a": [value, value, value],
            "b": [4, 5, 6],
        }
    )

    spark = SparkSession.builder.getOrCreate()  # type: ignore
    return spark.createDataFrame(pd_df)


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
        out_df = duckdb_conn.execute("SELECT * FROM my_schema.static_partitioned").fetch_df()
        assert out_df["a"].tolist() == ["1", "1", "1"]
        duckdb_conn.close()

        materialize(
            [static_partitioned],
            partition_key="blue",
            resources=resource_defs,
            run_config={"ops": {"my_schema__static_partitioned": {"config": {"value": "2"}}}},
        )

        duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))
        out_df = duckdb_conn.execute("SELECT * FROM my_schema.static_partitioned").fetch_df()
        assert sorted(out_df["a"].tolist()) == ["1", "1", "1", "2", "2", "2"]
        duckdb_conn.close()

        materialize(
            [static_partitioned],
            partition_key="red",
            resources=resource_defs,
            run_config={"ops": {"my_schema__static_partitioned": {"config": {"value": "3"}}}},
        )

        duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))
        out_df = duckdb_conn.execute("SELECT * FROM my_schema.static_partitioned").fetch_df()
        assert sorted(out_df["a"].tolist()) == ["2", "2", "2", "3", "3", "3"]

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
    metadata={"partition_expr": {"time": "CAST(time as TIMESTAMP)", "color": "color"}},
    config_schema={"value": str},
)
def multi_partitioned(context) -> SparkDF:
    partition = context.partition_key.keys_by_dimension
    value = context.op_config["value"]
    pd_df = pd.DataFrame(
        {
            "color": [partition["color"], partition["color"], partition["color"]],
            "time": [partition["time"], partition["time"], partition["time"]],
            "a": [value, value, value],
        }
    )

    spark = SparkSession.builder.getOrCreate()  # type: ignore
    return spark.createDataFrame(pd_df)


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
        out_df = duckdb_conn.execute("SELECT * FROM my_schema.multi_partitioned").fetch_df()
        assert out_df["a"].tolist() == ["1", "1", "1"]
        duckdb_conn.close()

        materialize(
            [multi_partitioned],
            partition_key=MultiPartitionKey({"time": "2022-01-01", "color": "blue"}),
            resources=resource_defs,
            run_config={"ops": {"my_schema__multi_partitioned": {"config": {"value": "2"}}}},
        )

        duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))
        out_df = duckdb_conn.execute("SELECT * FROM my_schema.multi_partitioned").fetch_df()
        assert sorted(out_df["a"].tolist()) == ["1", "1", "1", "2", "2", "2"]
        duckdb_conn.close()

        materialize(
            [multi_partitioned],
            partition_key=MultiPartitionKey({"time": "2022-01-02", "color": "red"}),
            resources=resource_defs,
            run_config={"ops": {"my_schema__multi_partitioned": {"config": {"value": "3"}}}},
        )

        duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))
        out_df = duckdb_conn.execute("SELECT * FROM my_schema.multi_partitioned").fetch_df()
        assert sorted(out_df["a"].tolist()) == ["1", "1", "1", "2", "2", "2", "3", "3", "3"]
        duckdb_conn.close()

        materialize(
            [multi_partitioned],
            partition_key=MultiPartitionKey({"time": "2022-01-01", "color": "red"}),
            resources=resource_defs,
            run_config={"ops": {"my_schema__multi_partitioned": {"config": {"value": "4"}}}},
        )

        duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))
        out_df = duckdb_conn.execute("SELECT * FROM my_schema.multi_partitioned").fetch_df()
        assert sorted(out_df["a"].tolist()) == ["2", "2", "2", "3", "3", "3", "4", "4", "4"]

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
def dynamic_partitioned(context) -> SparkDF:
    partition = context.asset_partition_key_for_output()
    value = context.op_config["value"]
    pd_df = pd.DataFrame(
        {
            "fruit": [partition, partition, partition],
            "a": [value, value, value],
        }
    )

    spark = SparkSession.builder.getOrCreate()  # type: ignore
    return spark.createDataFrame(pd_df)


def test_dynamic_partition(tmp_path, io_managers):
    for io_manager in io_managers:
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

            duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))
            out_df = duckdb_conn.execute("SELECT * FROM my_schema.dynamic_partitioned").fetch_df()
            assert out_df["a"].tolist() == ["1", "1", "1"]
            duckdb_conn.close()

            instance.add_dynamic_partitions(dynamic_fruits.name, ["orange"])

            materialize(
                [dynamic_partitioned],
                partition_key="orange",
                resources=resource_defs,
                instance=instance,
                run_config={"ops": {"my_schema__dynamic_partitioned": {"config": {"value": "2"}}}},
            )

            duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))
            out_df = duckdb_conn.execute("SELECT * FROM my_schema.dynamic_partitioned").fetch_df()
            assert sorted(out_df["a"].tolist()) == ["1", "1", "1", "2", "2", "2"]
            duckdb_conn.close()

            materialize(
                [dynamic_partitioned],
                partition_key="apple",
                resources=resource_defs,
                instance=instance,
                run_config={"ops": {"my_schema__dynamic_partitioned": {"config": {"value": "3"}}}},
            )

            duckdb_conn = duckdb.connect(database=os.path.join(tmp_path, "unit_test.duckdb"))
            out_df = duckdb_conn.execute("SELECT * FROM my_schema.dynamic_partitioned").fetch_df()
            assert sorted(out_df["a"].tolist()) == ["2", "2", "2", "3", "3", "3"]

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
    def self_dependent_asset(context, self_dependent_asset: SparkDF) -> SparkDF:
        key = context.asset_partition_key_for_output()

        if not self_dependent_asset.isEmpty():
            pd_df = self_dependent_asset.toPandas()
            assert len(pd_df.index) == 3
            assert (pd_df["key"] == context.op_config["last_partition_key"]).all()
        else:
            assert context.op_config["last_partition_key"] == "NA"
        value = context.op_config["value"]
        pd_df = pd.DataFrame(
            {
                "key": [key, key, key],
                "a": [value, value, value],
            }
        )

        spark = SparkSession.builder.getOrCreate()  # type: ignore
        return spark.createDataFrame(pd_df)

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
        out_df = duckdb_conn.execute("SELECT * FROM my_schema.self_dependent_asset").fetch_df()

        assert out_df["a"].tolist() == ["1", "1", "1"]
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
        out_df = duckdb_conn.execute("SELECT * FROM my_schema.self_dependent_asset").fetch_df()

        assert out_df["a"].tolist() == ["1", "1", "1", "2", "2", "2"]

        # drop table so we start with an empty db for the next io manager
        duckdb_conn.execute("DELETE FROM my_schema.self_dependent_asset")
        duckdb_conn.close()
