"""Unit tests for ClickHouse SQL generation (no Docker)."""

from datetime import datetime
from unittest.mock import MagicMock

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
    query, params = ClickhouseDbClient.get_select_statement_and_params(
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
    assert (
        query == "SELECT `apple`, `banana` FROM `schema1`.`table1` WHERE\n`my_timestamp_col` >= "
        "%(partition_0_start)s AND `my_timestamp_col` < %(partition_0_end)s"
    )
    assert params == {
        "partition_0_start": "2020-01-02 00:00:00",
        "partition_0_end": "2020-02-03 00:00:00",
    }


def test_get_select_statement_static_partitioned():
    query, params = ClickhouseDbClient.get_select_statement_and_params(
        TableSlice(
            schema="schema1",
            table="table1",
            partition_dimensions=[
                TablePartitionDimension(partition_expr="my_fruit_col", partitions=["apple"])
            ],
            columns=["apple", "banana"],
        )
    )
    assert (
        query == "SELECT `apple`, `banana` FROM `schema1`.`table1` WHERE\n`my_fruit_col` IN "
        "%(partition_0_values)s"
    )
    assert params == {"partition_0_values": ("apple",)}


def test_get_select_statement_static_partition_uses_params_for_quotes_and_backslashes():
    query, params = ClickhouseDbClient.get_select_statement_and_params(
        TableSlice(
            schema="schema1",
            table="table1",
            partition_dimensions=[
                TablePartitionDimension(
                    partition_expr="my_fruit_col", partitions=["it's", "\\' OR 1=1 --"]
                )
            ],
        )
    )
    assert (
        query == "SELECT * FROM `schema1`.`table1` WHERE\n`my_fruit_col` IN %(partition_0_values)s"
    )
    assert params == {"partition_0_values": ("it's", "\\' OR 1=1 --")}


def test_delete_table_slice_static_partition_uses_params():
    connection = MagicMock()

    ClickhouseDbClient.delete_table_slice(
        MagicMock(),
        TableSlice(
            schema="schema1",
            table="table1",
            partition_dimensions=[
                TablePartitionDimension(
                    partition_expr="my_fruit_col", partitions=["it's", "\\' OR 1=1 --"]
                )
            ],
        ),
        connection,
    )

    connection.execute.assert_called_once_with(
        "ALTER TABLE `schema1`.`table1` DELETE WHERE `my_fruit_col` IN %(partition_0_values)s "
        "SETTINGS mutations_sync = 1",
        {"partition_0_values": ("it's", "\\' OR 1=1 --")},
    )


def test_get_select_statement_multi_partitioned():
    query, params = ClickhouseDbClient.get_select_statement_and_params(
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
    assert (
        query == "SELECT * FROM `schema1`.`table1` WHERE\n`my_fruit_col` IN %(partition_0_values)s "
        "AND\n`my_timestamp_col` >= %(partition_1_start)s AND `my_timestamp_col` < "
        "%(partition_1_end)s"
    )
    assert params == {
        "partition_0_values": ("apple",),
        "partition_1_start": "2020-01-02 00:00:00",
        "partition_1_end": "2020-02-03 00:00:00",
    }
