"""Unit tests for ClickHouse SQL generation (no Docker)."""

from datetime import datetime

from dagster._core.definitions.partitions.utils import TimeWindow
from dagster._core.storage.db_io_manager import TablePartitionDimension, TableSlice
from dagster_clickhouse.db_client import ClickhouseDbClient, format_clickhouse_table_fqn


def test_get_table_name():
    assert ClickhouseDbClient.get_table_name(TableSlice(schema="db1", table="t1")) == "db1.t1"


def test_format_clickhouse_table_fqn():
    assert (
        format_clickhouse_table_fqn(TableSlice(schema="schema1", table="table1"))
        == "`schema1`.`table1`"
    )


def test_get_select_statement():
    assert (
        ClickhouseDbClient.get_select_statement(TableSlice(schema="schema1", table="table1"))
        == "SELECT * FROM `schema1`.`table1`"
    )


def test_get_select_statement_columns():
    assert (
        ClickhouseDbClient.get_select_statement(
            TableSlice(
                schema="schema1",
                table="table1",
                columns=["apple", "banana"],
            )
        )
        == "SELECT `apple`, `banana` FROM `schema1`.`table1`"
    )


def test_get_select_statement_partitioned():
    assert (
        ClickhouseDbClient.get_select_statement(
            TableSlice(
                schema="schema1",
                table="table1",
                partition_dimensions=[
                    TablePartitionDimension(
                        partitions=TimeWindow(datetime(2020, 1, 2), datetime(2020, 2, 3)),
                        partition_expr="my_timestamp_col",
                    )
                ],
                columns=["apple", "banana"],
            )
        )
        == "SELECT `apple`, `banana` FROM `schema1`.`table1` WHERE\n`my_timestamp_col` >= '2020-01-02"
        " 00:00:00' AND `my_timestamp_col` < '2020-02-03 00:00:00'"
    )


def test_get_select_statement_static_partitioned():
    assert (
        ClickhouseDbClient.get_select_statement(
            TableSlice(
                schema="schema1",
                table="table1",
                partition_dimensions=[
                    TablePartitionDimension(partition_expr="my_fruit_col", partitions=["apple"])
                ],
                columns=["apple", "banana"],
            )
        )
        == "SELECT `apple`, `banana` FROM `schema1`.`table1` WHERE\n`my_fruit_col` IN ('apple')"
    )


def test_get_select_statement_multi_partitioned():
    assert (
        ClickhouseDbClient.get_select_statement(
            TableSlice(
                schema="schema1",
                table="table1",
                partition_dimensions=[
                    TablePartitionDimension(partition_expr="my_fruit_col", partitions=["apple"]),
                    TablePartitionDimension(
                        partitions=TimeWindow(datetime(2020, 1, 2), datetime(2020, 2, 3)),
                        partition_expr="my_timestamp_col",
                    ),
                ],
            )
        )
        == "SELECT * FROM `schema1`.`table1` WHERE\n`my_fruit_col` IN ('apple') AND\n`my_timestamp_col` >="
        " '2020-01-02 00:00:00' AND `my_timestamp_col` < '2020-02-03 00:00:00'"
    )
