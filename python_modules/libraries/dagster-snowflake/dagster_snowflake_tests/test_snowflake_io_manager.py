from datetime import datetime

from dagster_snowflake.db_io_manager import TablePartition, TableSlice
from dagster_snowflake.snowflake_io_manager import (
    SnowflakeDbClient,
    _get_cleanup_statement,
)
from dagster import op


def test_get_select_statement():
    assert (
        SnowflakeDbClient.get_select_statement(
            TableSlice(database="database_abc", schema="schema1", table="table1")
        )
        == "SELECT * FROM database_abc.schema1.table1"
    )


def test_get_select_statement_columns():
    assert (
        SnowflakeDbClient.get_select_statement(
            TableSlice(
                database="database_abc",
                schema="schema1",
                table="table1",
                columns=["apple", "banana"],
            )
        )
        == "SELECT apple, banana FROM database_abc.schema1.table1"
    )


def test_get_select_statement_partitioned():
    assert SnowflakeDbClient.get_select_statement(
        TableSlice(
            database="database_abc",
            schema="schema1",
            table="table1",
            partition=TablePartition(
                time_window=(datetime(2020, 1, 2), datetime(2020, 2, 3)),
                partition_expr="my_timestamp_col",
            ),
            columns=["apple", "banana"],
        )
    ) == (
        "SELECT apple, banana FROM database_abc.schema1.table1\n"
        "WHERE my_timestamp_col BETWEEN '2020-01-02 00:00:00' AND '2020-02-03 00:00:00'"
    )


def test_get_cleanup_statement():
    assert (
        _get_cleanup_statement(
            TableSlice(database="database_abc", schema="schema1", table="table1")
        )
        == "DELETE FROM database_abc.schema1.table1"
    )


def test_get_cleanup_statement_partitioned():
    assert _get_cleanup_statement(
        TableSlice(
            database="database_abc",
            schema="schema1",
            table="table1",
            partition=TablePartition(
                time_window=(datetime(2020, 1, 2), datetime(2020, 2, 3)),
                partition_expr="my_timestamp_col",
            ),
        )
    ) == (
        "DELETE FROM database_abc.schema1.table1\n"
        "WHERE my_timestamp_col BETWEEN '2020-01-02 00:00:00' AND '2020-02-03 00:00:00'"
    )
