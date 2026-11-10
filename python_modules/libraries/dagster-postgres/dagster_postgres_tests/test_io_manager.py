from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from dagster import InputContext, OutputContext, build_output_context
from dagster._check import CheckError
from dagster._core.definitions.partitions.utils import TimeWindow
from dagster._core.storage.db_io_manager import (
    DbIOManager,
    DbTypeHandler,
    TablePartitionDimension,
    TableSlice,
)
from dagster_postgres import PostgresIOManager, build_postgres_io_manager
from dagster_postgres.io_manager import (
    PostgresDbClient,
    _get_cleanup_statement,
    format_postgres_table_fqn,
    postgres_url_from_resource_config,
    quote_identifier,
)


class DummyTypeHandler(DbTypeHandler[dict]):
    def handle_output(self, context: OutputContext, table_slice: TableSlice, obj, connection):
        return None

    def load_input(self, context: InputContext, table_slice: TableSlice, connection):
        return {}

    @property
    def supported_types(self):
        return [dict]


class DummyPostgresIOManager(PostgresIOManager):
    @staticmethod
    def type_handlers() -> Sequence[DbTypeHandler]:
        return [DummyTypeHandler()]


def test_quote_identifier():
    assert quote_identifier("my_table") == '"my_table"'
    assert quote_identifier("MyTable") == '"MyTable"'
    assert quote_identifier('odd"name') == '"odd""name"'


def test_format_table_fqn():
    table_slice = TableSlice(table="my_table", schema="my_schema", database="my_db")
    assert format_postgres_table_fqn(table_slice) == '"my_schema"."my_table"'
    assert PostgresDbClient.get_table_name(table_slice) == "my_schema.my_table"


def test_get_select_statement():
    assert (
        PostgresDbClient.get_select_statement(
            TableSlice(database="my_db", schema="schema1", table="table1")
        )
        == 'SELECT * FROM "schema1"."table1"'
    )


def test_get_select_statement_columns():
    assert (
        PostgresDbClient.get_select_statement(
            TableSlice(
                database="my_db",
                schema="schema1",
                table="table1",
                columns=["apple", "banana"],
            )
        )
        == 'SELECT "apple", "banana" FROM "schema1"."table1"'
    )


def test_get_select_statement_time_window_partitioned():
    assert (
        PostgresDbClient.get_select_statement(
            TableSlice(
                database="my_db",
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
        == 'SELECT "apple", "banana" FROM "schema1"."table1" WHERE\nmy_timestamp_col >='
        " '2020-01-02 00:00:00' AND my_timestamp_col < '2020-02-03 00:00:00'"
    )


def test_get_select_statement_static_partitioned():
    assert (
        PostgresDbClient.get_select_statement(
            TableSlice(
                database="my_db",
                schema="schema1",
                table="table1",
                partition_dimensions=[
                    TablePartitionDimension(partition_expr="my_fruit_col", partitions=["apple"])
                ],
                columns=["apple", "banana"],
            )
        )
        == 'SELECT "apple", "banana" FROM "schema1"."table1" WHERE\nmy_fruit_col in (\'apple\')'
    )


def test_get_select_statement_multiple_static_partitions():
    assert (
        PostgresDbClient.get_select_statement(
            TableSlice(
                database="my_db",
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
        == 'SELECT "fruit_col", "other_col" FROM "schema1"."table1" WHERE\nfruit_col in'
        " ('apple', 'banana')"
    )


def test_get_select_statement_multi_partitioned():
    assert (
        PostgresDbClient.get_select_statement(
            TableSlice(
                database="my_db",
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
        == 'SELECT * FROM "schema1"."table1" WHERE\nmy_fruit_col in (\'apple\') AND\n'
        "my_timestamp_col >= '2020-01-02 00:00:00' AND my_timestamp_col < '2020-02-03 00:00:00'"
    )


def test_get_cleanup_statement():
    assert (
        _get_cleanup_statement(TableSlice(database="my_db", schema="schema1", table="table1"))
        == 'DELETE FROM "schema1"."table1"'
    )
    assert (
        _get_cleanup_statement(
            TableSlice(
                database="my_db",
                schema="schema1",
                table="table1",
                partition_dimensions=[
                    TablePartitionDimension(partition_expr="my_fruit_col", partitions=["apple"])
                ],
            )
        )
        == 'DELETE FROM "schema1"."table1" WHERE\nmy_fruit_col in (\'apple\')'
    )


def test_time_window_bounds_keep_utc_offset():
    new_york = timezone(timedelta(hours=-5))
    window = TimeWindow(
        datetime(2020, 1, 2, tzinfo=new_york), datetime(2020, 1, 3, tzinfo=new_york)
    )
    table_slice = TableSlice(
        database="my_db",
        schema="schema1",
        table="table1",
        partition_dimensions=[
            TablePartitionDimension(partitions=window, partition_expr="my_timestamp_col")
        ],
    )
    assert (
        _get_cleanup_statement(table_slice)
        == 'DELETE FROM "schema1"."table1" WHERE\nmy_timestamp_col >='
        " '2020-01-02 00:00:00-0500' AND my_timestamp_col < '2020-01-03 00:00:00-0500'"
    )


def test_delete_table_slice_sends_statement_without_bind_parsing():
    connection = MagicMock()
    connection.execute.return_value.scalar.return_value = "schema1.table1"
    cursor = connection.connection.cursor.return_value
    table_slice = TableSlice(
        database="my_db",
        schema="schema1",
        table="table1",
        partition_dimensions=[
            TablePartitionDimension(partition_expr="my_fruit_col", partitions=[":foo"])
        ],
    )

    PostgresDbClient.delete_table_slice(build_output_context(), table_slice, connection)

    cursor.execute.assert_called_once_with(
        'DELETE FROM "schema1"."table1" WHERE\nmy_fruit_col in (\':foo\')'
    )
    cursor.close.assert_called_once()


def test_delete_table_slice_missing_table():
    connection = MagicMock()
    connection.execute.return_value.scalar.return_value = None

    PostgresDbClient.delete_table_slice(
        build_output_context(),
        TableSlice(database="my_db", schema="schema1", table="table1"),
        connection,
    )

    connection.connection.cursor.assert_not_called()


def test_postgres_url_from_resource_config():
    assert (
        postgres_url_from_resource_config({"postgres_url": "postgresql://u:p@host:5432/db"})
        == "postgresql://u:p@host:5432/db"
    )
    assert (
        postgres_url_from_resource_config(
            {
                "hostname": "localhost",
                "username": "test",
                "password": "secret",
                "db_name": "analytics",
                "port": 5433,
                "params": {"sslmode": "require"},
            }
        )
        == "postgresql://test:secret@localhost:5433/analytics?sslmode=require"
    )
    assert (
        postgres_url_from_resource_config({"hostname": "localhost", "username": "test"})
        == "postgresql://test@localhost:5432/"
    )
    with pytest.raises(CheckError):
        postgres_url_from_resource_config({"username": "test"})


def test_pythonic_io_manager_config():
    io_manager = DummyPostgresIOManager(
        hostname="localhost", username="test", db_name="analytics", schema="my_schema"
    )
    assert io_manager.schema_ == "my_schema"
    db_io_manager = io_manager.create_io_manager(None)
    assert isinstance(db_io_manager, DbIOManager)
    assert isinstance(db_io_manager._db_client, PostgresDbClient)  # noqa: SLF001
    assert db_io_manager._schema == "my_schema"  # noqa: SLF001

    context = build_output_context(
        resource_config={
            "hostname": "localhost",
            "username": "test",
            "db_name": "analytics",
            "port": 5432,
            "params": {},
            "scheme": "postgresql",
        }
    )
    assert (
        postgres_url_from_resource_config(context.resource_config)
        == "postgresql://test@localhost:5432/analytics"
    )


def test_legacy_io_manager_config():
    io_manager_def = build_postgres_io_manager([DummyTypeHandler()])
    assert "postgres_url" in io_manager_def.config_schema.as_field().config_type.fields  # type: ignore
    assert "schema" in io_manager_def.config_schema.as_field().config_type.fields  # type: ignore
