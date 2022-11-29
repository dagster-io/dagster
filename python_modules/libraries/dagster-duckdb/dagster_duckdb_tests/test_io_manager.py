from datetime import datetime

from dagster_duckdb.io_manager import DuckDbClient, _get_cleanup_statement

from dagster._core.storage.db_io_manager import TablePartition, TableSlice


def test_get_select_statement():
    assert (
        DuckDbClient.get_select_statement(TableSlice(schema="schema1", table="table1"))
        == "SELECT * FROM schema1.table1"
    )


def test_get_select_statement_columns():
    assert (
        DuckDbClient.get_select_statement(
            TableSlice(
                schema="schema1",
                table="table1",
                columns=["apple", "banana"],
            )
        )
        == "SELECT apple, banana FROM schema1.table1"
    )


def test_get_select_statement_partitioned():
    assert DuckDbClient.get_select_statement(
        TableSlice(
            schema="schema1",
            table="table1",
            partition=TablePartition(
                time_window=(datetime(2020, 1, 2), datetime(2020, 2, 3)),
                partition_expr="my_timestamp_col",
            ),
            columns=["apple", "banana"],
        )
    ) == (
        "SELECT apple, banana FROM schema1.table1\n"
        "WHERE my_timestamp_col >= '2020-01-02 00:00:00' AND my_timestamp_col < '2020-02-03 00:00:00'"
    )


def test_get_cleanup_statement():
    assert (
        _get_cleanup_statement(TableSlice(schema="schema1", table="table1"))
        == "DELETE FROM schema1.table1"
    )


def test_get_cleanup_statement_partitioned():
    assert _get_cleanup_statement(
        TableSlice(
            schema="schema1",
            table="table1",
            partition=TablePartition(
                time_window=(datetime(2020, 1, 2), datetime(2020, 2, 3)),
                partition_expr="my_timestamp_col",
            ),
        )
    ) == (
        "DELETE FROM schema1.table1\n"
        "WHERE my_timestamp_col >= '2020-01-02 00:00:00' AND my_timestamp_col < '2020-02-03 00:00:00'"
    )
