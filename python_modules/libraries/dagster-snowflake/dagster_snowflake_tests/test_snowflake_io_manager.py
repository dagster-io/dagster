from datetime import datetime
from unittest import mock

from dagster import TimeWindow
from dagster._core.definitions import materialize
from dagster._core.definitions.decorators import asset
from dagster._core.storage.db_io_manager import DbTypeHandler, TablePartitionDimension, TableSlice
from dagster_snowflake.snowflake_io_manager import (
    SnowflakeDbClient,
    SnowflakeIOManager,
    _get_cleanup_statement,
)


class PassTypeHandler(DbTypeHandler[int]):
    def handle_output(self, *args, **kwargs):
        return None

    def load_input(self, *args, **kwargs):
        return None

    @property
    def supported_types(self):
        return [int]


class TestSnowflakeIOManager(SnowflakeIOManager):
    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def type_handlers(self):
        return [PassTypeHandler()]


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


def test_get_select_statement_time_partitioned():
    assert (
        SnowflakeDbClient.get_select_statement(
            TableSlice(
                database="database_abc",
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
        == "SELECT apple, banana FROM database_abc.schema1.table1 WHERE\nmy_timestamp_col >="
        " '2020-01-02 00:00:00' AND my_timestamp_col < '2020-02-03 00:00:00'"
    )


def test_get_select_statement_static_partitioned():
    assert (
        SnowflakeDbClient.get_select_statement(
            TableSlice(
                database="database_abc",
                schema="schema1",
                table="table1",
                partition_dimensions=[
                    TablePartitionDimension(partition_expr="my_fruit_col", partitions=["apple"])
                ],
                columns=["apple", "banana"],
            )
        )
        == "SELECT apple, banana FROM database_abc.schema1.table1 WHERE\nmy_fruit_col in ('apple')"
    )


def test_get_select_statement_multiple_static_partitions():
    assert (
        SnowflakeDbClient.get_select_statement(
            TableSlice(
                database="database_abc",
                schema="schema1",
                table="table1",
                partition_dimensions=[
                    TablePartitionDimension(
                        partition_expr="fruit_col", partitions=["apple", "banana"]
                    )
                ],
                columns=["fruit_col", "other_col"],
            )
        )
        == "SELECT fruit_col, other_col FROM database_abc.schema1.table1 WHERE\nfruit_col in"
        " ('apple', 'banana')"
    )


def test_get_select_statement_multi_partitioned():
    assert (
        SnowflakeDbClient.get_select_statement(
            TableSlice(
                database="database_abc",
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
        == "SELECT * FROM database_abc.schema1.table1 WHERE\nmy_fruit_col in ('apple')"
        " AND\nmy_timestamp_col >= '2020-01-02 00:00:00' AND my_timestamp_col < '2020-02-03"
        " 00:00:00'"
    )


def test_get_cleanup_statement():
    assert (
        _get_cleanup_statement(
            TableSlice(database="database_abc", schema="schema1", table="table1")
        )
        == "DELETE FROM database_abc.schema1.table1"
    )


def test_get_cleanup_statement_time_partitioned():
    assert (
        _get_cleanup_statement(
            TableSlice(
                database="database_abc",
                schema="schema1",
                table="table1",
                partition_dimensions=[
                    TablePartitionDimension(
                        partitions=TimeWindow(datetime(2020, 1, 2), datetime(2020, 2, 3)),
                        partition_expr="my_timestamp_col",
                    )
                ],
            )
        )
        == "DELETE FROM database_abc.schema1.table1 WHERE\nmy_timestamp_col >= '2020-01-02"
        " 00:00:00' AND my_timestamp_col < '2020-02-03 00:00:00'"
    )


def test_get_cleanup_statement_static_partitioned():
    assert (
        _get_cleanup_statement(
            TableSlice(
                database="database_abc",
                schema="schema1",
                table="table1",
                partition_dimensions=[
                    TablePartitionDimension(partition_expr="my_fruit_col", partitions=["apple"])
                ],
            )
        )
        == "DELETE FROM database_abc.schema1.table1 WHERE\nmy_fruit_col in ('apple')"
    )


def test_get_cleanup_statement_multi_partitioned():
    assert (
        _get_cleanup_statement(
            TableSlice(
                database="database_abc",
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
        == "DELETE FROM database_abc.schema1.table1 WHERE\nmy_fruit_col in ('apple')"
        " AND\nmy_timestamp_col >= '2020-01-02 00:00:00' AND my_timestamp_col < '2020-02-03"
        " 00:00:00'"
    )


def test_io_manager_snowflake_additional_snowflake_connection_args():
    """Tests that args passed to additional_snowflake_connection_args are correctly forwarded to
    snowflake.connector.connect.
    """
    with mock.patch("snowflake.connector.connect") as snowflake_conn_mock:
        io_mgr = TestSnowflakeIOManager(
            account="account",
            user="user",
            password="password",
            database="TESTDB",
            schema="TESTSCHEMA",
            additional_snowflake_connection_args={"foo": "bar"},
        )

        @asset
        def return_one():
            return 1

        materialize([return_one], resources={"io_manager": io_mgr})
        assert snowflake_conn_mock.call_count == 1
        assert snowflake_conn_mock.call_args[1]["foo"] == "bar"
