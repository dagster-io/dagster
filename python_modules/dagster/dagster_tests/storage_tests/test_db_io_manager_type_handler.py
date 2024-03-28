from contextlib import contextmanager
from enum import Enum
from typing import Iterator

import pandas as pd
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
    fs_io_manager,
    graph,
    instance_for_test,
    materialize,
    op,
)
from dagster._check import CheckError


class DataFrameType(Enum):
    PANDAS = "pandas"
    PYSPARK = "pyspark"
    POLARS = "polars"


class TemplateTypeHandlerTestSuite:
    @property
    def df_format(self) -> DataFrameType:
        """Returns the type of dataframe this test suite will use."""
        raise NotImplementedError("All test suites must implement df_format.")

    @property
    def database(self) -> str:
        raise NotImplementedError("All test suites must implement database")

    @property
    def schema(self) -> str:
        raise NotImplementedError("All test suites must implement schema")

    def io_managers(self):
        """Returns a list of I/O managers to test. In most cases there will be one pythonic style I/O manager, and one old-stype I/O manager."""
        raise NotImplementedError("All test suites must implement io_managers.")

    @contextmanager
    def temporary_table_name(self) -> Iterator[str]:
        """Returns the name of the created table."""
        raise NotImplementedError("All test suites must implement create_temporary_table")

    @contextmanager
    def get_db_connection(self):
        """Returns a connection to the DB to assert data was stored."""
        raise NotImplementedError("All test suites must implement get_db_connection")

    def select_all_from_table(self, table_name) -> pd.DataFrame:
        raise NotImplementedError("All test suites must implement select_all_from_table")

    def test_not_supported_type(self):
        @asset
        def not_supported() -> int:
            return 1

        for io_manager in self.io_managers():
            with pytest.raises(
                CheckError,
                match="does not have a handler for type '<class 'int'>'",
            ):
                materialize([not_supported], resources={"io_manager": io_manager})

    # TODO this test is strange, since the schema is like the asset key? idk
    @pytest.mark.skip
    def test_db_io_manager_with_ops(self):
        @op(out=Out(metadata={"schema": "a_df"}))
        def a_df() -> pd.DataFrame:
            return pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})

        @op(out=Out(metadata={"schema": "add_one"}))
        def add_one(df: pd.DataFrame) -> pd.DataFrame:
            return df + 1

        @graph
        def add_one_to_dataframe():
            add_one(a_df())

        for io_manager in self.io_managers():
            resource_defs = {"io_manager": io_manager}

            job = add_one_to_dataframe.to_job(resource_defs=resource_defs)

            # run the job twice to ensure that tables get properly deleted
            for _ in range(2):
                res = job.execute_in_process()

                with self.get_db_connection() as conn:
                    assert res.success
                    out_df = conn.execute("SELECT * FROM a_df.result").fetch_df()
                    assert out_df["A"].tolist() == [1, 2, 3]

                    out_df = conn.execute("SELECT * FROM add_one.result").fetch_df()
                    assert out_df["A"].tolist() == [2, 3, 4]

    @pytest.mark.skip
    def test_db_io_manager_with_assets(self):
        for io_manager in self.io_managers():
            with self.temporary_table_name() as table_1, self.temporary_table_name() as table_2:

                @asset(key_prefix=[self.schema], name=table_1)
                def b_df() -> pd.DataFrame:
                    return pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})

                @asset(
                    key_prefix=[self.schema],
                    name=table_2,
                    ins={"df": AssetIn([self.schema, table_1])},
                )
                def b_plus_one(df: pd.DataFrame) -> pd.DataFrame:
                    return df + 1

                resource_defs = {"io_manager": io_manager}

                # materialize asset twice to ensure that tables get properly deleted
                for _ in range(2):
                    res = materialize([b_df, b_plus_one], resources=resource_defs)
                    assert res.success
                    assert self.select_all_from_table(table_1)["A"].tolist() == [1, 2, 3]
                    assert self.select_all_from_table(table_2)["A"].tolist() == [2, 3, 4]

    def test_loading_columns(self):
        for io_manager in self.io_managers():
            with self.temporary_table_name() as table_1, self.temporary_table_name() as table_2:

                @asset(key_prefix=[self.schema], name=table_1)
                def b_df() -> pd.DataFrame:
                    return pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})

                @asset(
                    key_prefix=[self.schema],
                    ins={"df": AssetIn([self.schema, table_1], metadata={"columns": ["A"]})},
                    name=table_2,
                )
                def b_plus_one_columns(df: pd.DataFrame) -> pd.DataFrame:
                    return df + 1

                resource_defs = {"io_manager": io_manager}

                # materialize asset twice to ensure that tables get properly deleted
                for _ in range(2):
                    res = materialize([b_df, b_plus_one_columns], resources=resource_defs)
                    assert res.success

                    assert self.select_all_from_table(table_1)["A"].tolist() == [1, 2, 3]

                    out_df = self.select_all_from_table(table_2)
                    assert out_df["A"].tolist() == [2, 3, 4]
                    assert out_df.shape[1] == 1

    def test_time_window_partitioned(self):
        for io_manager in self.io_managers():
            with self.temporary_table_name() as table_name:
                partitions_def = DailyPartitionsDefinition(start_date="2022-01-01")

                @asset(
                    partitions_def=partitions_def,
                    key_prefix=[self.schema],
                    metadata={"partition_expr": "TIME"},
                    config_schema={"value": str},
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
                    key_prefix=[self.schema],
                    ins={"df": AssetIn([self.schema, table_name])},
                    io_manager_key="fs_io",
                )
                def downstream_partitioned(df: pd.DataFrame) -> None:
                    # assert that we only get the expected number of rows
                    assert len(df.index) == 3

                resource_defs = {"io_manager": io_manager, "fs_io": fs_io_manager}
                to_materialize = [daily_partitioned, downstream_partitioned]

                materialize(
                    to_materialize,
                    partition_key="2022-01-01",
                    resources=resource_defs,
                    run_config={
                        "ops": {f"{self.schema}__{table_name}": {"config": {"value": "1"}}}
                    },
                )

                assert self.select_all_from_table(table_name)["A"].tolist() == ["1", "1", "1"]

                materialize(
                    to_materialize,
                    partition_key="2022-01-02",
                    resources=resource_defs,
                    run_config={
                        "ops": {f"{self.schema}__{table_name}": {"config": {"value": "2"}}}
                    },
                )

                assert sorted(self.select_all_from_table(table_name)["A"].tolist()) == [
                    "1",
                    "1",
                    "1",
                    "2",
                    "2",
                    "2",
                ]

                materialize(
                    to_materialize,
                    partition_key="2022-01-01",
                    resources=resource_defs,
                    run_config={
                        "ops": {f"{self.schema}__{table_name}": {"config": {"value": "3"}}}
                    },
                )

                assert sorted(self.select_all_from_table(table_name)["A"].tolist()) == [
                    "2",
                    "2",
                    "2",
                    "3",
                    "3",
                    "3",
                ]

    def test_static_partitioned(self):
        for io_manager in self.io_managers():
            with self.temporary_table_name() as table_name:
                partitions_def = StaticPartitionsDefinition(["red", "yellow", "blue"])

                @asset(
                    partitions_def=partitions_def,
                    key_prefix=[self.schema],
                    metadata={"partition_expr": "COLOR"},
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
                    key_prefix=[self.schema],
                    ins={"df": AssetIn([self.schema, table_name])},
                    io_manager_key="fs_io",
                )
                def downstream_partitioned(df: pd.DataFrame) -> None:
                    # assert that we only get the expected number of rows
                    assert len(df.index) == 3

                resource_defs = {"io_manager": io_manager, "fs_io": fs_io_manager}
                to_materialize = [static_partitioned, downstream_partitioned]

                materialize(
                    to_materialize,
                    partition_key="red",
                    resources=resource_defs,
                    run_config={
                        "ops": {f"{self.schema}__{table_name}": {"config": {"value": "1"}}}
                    },
                )

                assert self.select_all_from_table(table_name)["A"].tolist() == ["1", "1", "1"]

                materialize(
                    to_materialize,
                    partition_key="blue",
                    resources=resource_defs,
                    run_config={
                        "ops": {f"{self.schema}__{table_name}": {"config": {"value": "2"}}}
                    },
                )

                assert sorted(self.select_all_from_table(table_name)["A"].tolist()) == [
                    "1",
                    "1",
                    "1",
                    "2",
                    "2",
                    "2",
                ]

                materialize(
                    to_materialize,
                    partition_key="red",
                    resources=resource_defs,
                    run_config={
                        "ops": {f"{self.schema}__{table_name}": {"config": {"value": "3"}}}
                    },
                )

                assert sorted(self.select_all_from_table(table_name)["A"].tolist()) == [
                    "2",
                    "2",
                    "2",
                    "3",
                    "3",
                    "3",
                ]

    def test_multi_partitioned(self):
        for io_manager in self.io_managers():
            with self.temporary_table_name() as table_name:
                partitions_def = MultiPartitionsDefinition(
                    {
                        "TIME": DailyPartitionsDefinition(start_date="2022-01-01"),
                        "COLOR": StaticPartitionsDefinition(["red", "yellow", "blue"]),
                    }
                )

                @asset(
                    partitions_def=partitions_def,
                    key_prefix=[self.schema],
                    metadata={"partition_expr": {"TIME": "TIME", "COLOR": "COLOR"}},
                    config_schema={"value": str},
                    name=table_name,
                )
                def multi_partitioned(context) -> pd.DataFrame:
                    partition = context.partition_key.keys_by_dimension
                    value = context.op_execution_context.op_config["value"]
                    partition_time = pd.Timestamp(partition["TIME"])
                    return pd.DataFrame(
                        {
                            "COLOR": [partition["COLOR"], partition["COLOR"], partition["COLOR"]],
                            "TIME": [partition_time, partition_time, partition_time],
                            "A": [value, value, value],
                        }
                    )

                @asset(
                    partitions_def=partitions_def,
                    key_prefix=[self.schema],
                    ins={"df": AssetIn([self.schema, table_name])},
                    io_manager_key="fs_io",
                )
                def downstream_partitioned(df: pd.DataFrame) -> None:
                    # assert that we only get the expected number of rows
                    assert len(df.index) == 3

                resource_defs = {"io_manager": io_manager, "fs_io": fs_io_manager}
                to_materialize = [multi_partitioned, downstream_partitioned]

                materialize(
                    to_materialize,
                    partition_key=MultiPartitionKey({"TIME": "2022-01-01", "COLOR": "red"}),
                    resources=resource_defs,
                    run_config={
                        "ops": {f"{self.schema}__{table_name}": {"config": {"value": "1"}}}
                    },
                )

                assert self.select_all_from_table(table_name)["A"].tolist() == ["1", "1", "1"]

                materialize(
                    to_materialize,
                    partition_key=MultiPartitionKey({"TIME": "2022-01-01", "COLOR": "blue"}),
                    resources=resource_defs,
                    run_config={
                        "ops": {f"{self.schema}__{table_name}": {"config": {"value": "2"}}}
                    },
                )
                assert sorted(self.select_all_from_table(table_name)["A"].tolist()) == [
                    "1",
                    "1",
                    "1",
                    "2",
                    "2",
                    "2",
                ]

                materialize(
                    to_materialize,
                    partition_key=MultiPartitionKey({"TIME": "2022-01-02", "COLOR": "red"}),
                    resources=resource_defs,
                    run_config={
                        "ops": {f"{self.schema}__{table_name}": {"config": {"value": "3"}}}
                    },
                )

                assert sorted(self.select_all_from_table(table_name)["A"].tolist()) == [
                    "1",
                    "1",
                    "1",
                    "2",
                    "2",
                    "2",
                    "3",
                    "3",
                    "3",
                ]

                materialize(
                    to_materialize,
                    partition_key=MultiPartitionKey({"TIME": "2022-01-01", "COLOR": "red"}),
                    resources=resource_defs,
                    run_config={
                        "ops": {f"{self.schema}__{table_name}": {"config": {"value": "4"}}}
                    },
                )

                assert sorted(self.select_all_from_table(table_name)["A"].tolist()) == [
                    "2",
                    "2",
                    "2",
                    "3",
                    "3",
                    "3",
                    "4",
                    "4",
                    "4",
                ]

    def test_dynamic_partitioned(self):
        for io_manager in self.io_managers():
            with self.temporary_table_name() as table_name:
                partitions_def = DynamicPartitionsDefinition(name="dynamic_fruits")

                @asset(
                    partitions_def=partitions_def,
                    key_prefix=[self.schema],
                    metadata={"partition_expr": "FRUIT"},
                    config_schema={"value": str},
                    name=table_name,
                )
                def dynamic_partitioned(context: AssetExecutionContext) -> pd.DataFrame:
                    partition = context.partition_key
                    value = context.op_execution_context.op_config["value"]
                    return pd.DataFrame(
                        {
                            "FRUIT": [partition, partition, partition],
                            "A": [value, value, value],
                        }
                    )

                @asset(
                    partitions_def=partitions_def,
                    key_prefix=[self.schema],
                    ins={"df": AssetIn([self.schema, table_name])},
                    io_manager_key="fs_io",
                )
                def downstream_partitioned(df: pd.DataFrame) -> None:
                    # assert that we only get the expected number of rows
                    assert len(df.index) == 3

                resource_defs = {"io_manager": io_manager, "fs_io": fs_io_manager}
                to_materialize = [dynamic_partitioned, downstream_partitioned]

                with instance_for_test() as instance:
                    instance.add_dynamic_partitions(partitions_def.name, ["apple"])

                    materialize(
                        to_materialize,
                        partition_key="apple",
                        resources=resource_defs,
                        instance=instance,
                        run_config={
                            "ops": {f"{self.schema}__{table_name}": {"config": {"value": "1"}}}
                        },
                    )

                    assert self.select_all_from_table(table_name)["A"].tolist() == ["1", "1", "1"]

                    instance.add_dynamic_partitions(partitions_def.name, ["orange"])

                    materialize(
                        to_materialize,
                        partition_key="orange",
                        resources=resource_defs,
                        instance=instance,
                        run_config={
                            "ops": {f"{self.schema}__{table_name}": {"config": {"value": "2"}}}
                        },
                    )

                    assert sorted(self.select_all_from_table(table_name)["A"].tolist()) == [
                        "1",
                        "1",
                        "1",
                        "2",
                        "2",
                        "2",
                    ]

                    materialize(
                        to_materialize,
                        partition_key="apple",
                        resources=resource_defs,
                        instance=instance,
                        run_config={
                            "ops": {f"{self.schema}__{table_name}": {"config": {"value": "3"}}}
                        },
                    )
                    assert sorted(self.select_all_from_table(table_name)["A"].tolist()) == [
                        "2",
                        "2",
                        "2",
                        "3",
                        "3",
                        "3",
                    ]

    def test_self_dependent_asset(self):
        for io_manager in self.io_managers():
            with self.temporary_table_name() as table_name:
                partitions_def = DailyPartitionsDefinition(start_date="2023-01-01")

                @asset(
                    partitions_def=partitions_def,
                    key_prefix=[self.schema],
                    ins={
                        "self_dependent_asset": AssetIn(
                            key=AssetKey([self.schema, table_name]),
                            partition_mapping=TimeWindowPartitionMapping(
                                start_offset=-1, end_offset=-1
                            ),
                        ),
                    },
                    metadata={
                        "partition_expr": "TIME",
                    },
                    config_schema={"value": str, "last_partition_key": str},
                    name=table_name,
                )
                def self_dependent_asset(
                    context: AssetExecutionContext, self_dependent_asset: pd.DataFrame
                ) -> pd.DataFrame:
                    if not self_dependent_asset.empty:
                        assert len(self_dependent_asset.index) == 3
                        assert (
                            self_dependent_asset[
                                "TIME"
                            ]  # TODO need to fix snowflake io manager to keep column casing consistent
                            == pd.Timestamp(
                                context.op_execution_context.op_config["last_partition_key"]
                            )
                        ).all()
                    else:
                        assert context.op_execution_context.op_config["last_partition_key"] == "NA"

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
                    key_prefix=[self.schema],
                    ins={"df": AssetIn([self.schema, table_name])},
                    io_manager_key="fs_io",
                )
                def downstream_partitioned(df: pd.DataFrame) -> None:
                    # assert that we only get the expected number of rows
                    assert len(df.index) == 3

                resource_defs = {"io_manager": io_manager, "fs_io": fs_io_manager}
                to_materialize = [self_dependent_asset, downstream_partitioned]

                materialize(
                    to_materialize,
                    partition_key="2023-01-01",
                    resources=resource_defs,
                    run_config={
                        "ops": {
                            f"{self.schema}__{table_name}": {
                                "config": {"value": "1", "last_partition_key": "NA"}
                            }
                        }
                    },
                )

                assert self.select_all_from_table(table_name)["A"].tolist() == ["1", "1", "1"]

                materialize(
                    to_materialize,
                    partition_key="2023-01-02",
                    resources=resource_defs,
                    run_config={
                        "ops": {
                            f"{self.schema}__{table_name}": {
                                "config": {"value": "2", "last_partition_key": "2023-01-01"}
                            }
                        }
                    },
                )

                assert self.select_all_from_table(table_name)["A"].tolist() == [
                    "1",
                    "1",
                    "1",
                    "2",
                    "2",
                    "2",
                ]

    def test_quoted_identifiers_asset(self):
        for io_manager in self.io_managers():
            with self.temporary_table_name() as table_name:

                @asset(
                    key_prefix=[self.schema],
                    name=table_name,
                )
                def illegal_column_name(context: AssetExecutionContext):
                    return pd.DataFrame(
                        {
                            "5foo": [1, 2, 3],  # columns that start with numbers need to be quoted
                            "column with a space": [1, 2, 3],
                            "column_with_punctuation!": [1, 2, 3],
                            "by": [1, 2, 3],  # reserved
                        }
                    )

                resource_defs = {"io_manager": io_manager}
                res = materialize(
                    [illegal_column_name],
                    resources=resource_defs,
                )

                assert res.success
