from datetime import datetime

from dagster._core.storage.db_io_manager import TablePartitionDimension, TableSlice
from dagster_gcp.bigquery.io_manager import BigQueryClient, _get_cleanup_statement


def test_get_select_statement():
    assert (
        BigQueryClient.get_select_statement(
            TableSlice(database="db", schema="schema1", table="table1")
        )
        == "SELECT * FROM db.schema1.table1"
    )


def test_get_select_statement_columns():
    assert (
        BigQueryClient.get_select_statement(
            TableSlice(
                database="db",
                schema="schema1",
                table="table1",
                columns=["apple", "banana"],
            )
        )
        == "SELECT apple, banana FROM db.schema1.table1"
    )


def test_get_select_statement_partitioned():
    assert (
        BigQueryClient.get_select_statement(
            TableSlice(
                database="db",
                schema="schema1",
                table="table1",
                partition_dimensions=[
                    TablePartitionDimension(
                        partition=(datetime(2020, 1, 2), datetime(2020, 2, 3)),
                        partition_expr="my_timestamp_col",
                    )
                ],
                columns=["apple", "banana"],
            )
        )
        == "SELECT apple, banana FROM db.schema1.table1 WHERE\nmy_timestamp_col >= '2020-01-02"
        " 00:00:00' AND my_timestamp_col < '2020-02-03 00:00:00'"
    )


def test_get_select_statement_static_partitioned():
    assert (
        BigQueryClient.get_select_statement(
            TableSlice(
                database="db",
                schema="schema1",
                table="table1",
                partition_dimensions=[
                    TablePartitionDimension(partition_expr="my_fruit_col", partition="apple")
                ],
                columns=["apple", "banana"],
            )
        )
        == "SELECT apple, banana FROM db.schema1.table1 WHERE\nmy_fruit_col = 'apple'"
    )


def test_get_select_statement_multi_partitioned():
    assert (
        BigQueryClient.get_select_statement(
            TableSlice(
                database="db",
                schema="schema1",
                table="table1",
                partition_dimensions=[
                    TablePartitionDimension(partition_expr="my_fruit_col", partition="apple"),
                    TablePartitionDimension(
                        partition=(datetime(2020, 1, 2), datetime(2020, 2, 3)),
                        partition_expr="my_timestamp_col",
                    ),
                ],
            )
        )
        == "SELECT * FROM db.schema1.table1 WHERE\nmy_fruit_col = 'apple' AND\nmy_timestamp_col >="
        " '2020-01-02 00:00:00' AND my_timestamp_col < '2020-02-03 00:00:00'"
    )


def test_get_cleanup_statement():
    assert (
        _get_cleanup_statement(TableSlice(database="db", schema="schema1", table="table1"))
        == "TRUNCATE TABLE db.schema1.table1"
    )


def test_get_cleanup_statement_partitioned():
    assert (
        _get_cleanup_statement(
            TableSlice(
                database="db",
                schema="schema1",
                table="table1",
                partition_dimensions=[
                    TablePartitionDimension(
                        partition=(datetime(2020, 1, 2), datetime(2020, 2, 3)),
                        partition_expr="my_timestamp_col",
                    )
                ],
            )
        )
        == "DELETE FROM db.schema1.table1 WHERE\nmy_timestamp_col >= '2020-01-02 00:00:00' AND"
        " my_timestamp_col < '2020-02-03 00:00:00'"
    )


def test_get_cleanup_statement_static_partitioned():
    assert (
        _get_cleanup_statement(
            TableSlice(
                database="db",
                schema="schema1",
                table="table1",
                partition_dimensions=[
                    TablePartitionDimension(partition_expr="my_fruit_col", partition="apple")
                ],
            )
        )
        == "DELETE FROM db.schema1.table1 WHERE\nmy_fruit_col = 'apple'"
    )


def test_get_cleanup_statement_multi_partitioned():
    assert (
        _get_cleanup_statement(
            TableSlice(
                database="db",
                schema="schema1",
                table="table1",
                partition_dimensions=[
                    TablePartitionDimension(partition_expr="my_fruit_col", partition="apple"),
                    TablePartitionDimension(
                        partition=(datetime(2020, 1, 2), datetime(2020, 2, 3)),
                        partition_expr="my_timestamp_col",
                    ),
                ],
            )
        )
        == "DELETE FROM db.schema1.table1 WHERE\nmy_fruit_col = 'apple' AND\nmy_timestamp_col >="
        " '2020-01-02 00:00:00' AND my_timestamp_col < '2020-02-03 00:00:00'"
    )
