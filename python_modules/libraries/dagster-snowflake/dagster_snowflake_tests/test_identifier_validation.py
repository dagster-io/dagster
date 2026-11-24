import re
from collections.abc import Callable
from unittest import mock

import pytest
from dagster import DagsterInvariantViolationError, asset, build_output_context, materialize
from dagster._core.storage.db_io_manager import DbTypeHandler, TableSlice
from dagster_snowflake import fetch_last_updated_timestamps
from dagster_snowflake.components.dbt_project.component import (
    build_information_schema_columns_sql,
    build_information_schema_tables_sql,
)
from dagster_snowflake.snowflake_io_manager import (
    SnowflakeDbClient,
    SnowflakeIOManager,
    _get_cleanup_statement,
)

UNSAFE_NAMES = ["t; drop table x", "t --", "t'", 't"', "my table", "t()", "1t", "$t"]


def table_slice_with(field: str, name: str) -> TableSlice:
    names = {"database": "TESTDB", "schema": "TESTSCHEMA", "table": "MY_TABLE", field: name}
    return TableSlice(database=names["database"], schema=names["schema"], table=names["table"])


render_statement = pytest.mark.parametrize(
    ("render", "verb"),
    [(SnowflakeDbClient.get_select_statement, "SELECT *"), (_get_cleanup_statement, "DELETE")],
    ids=["select", "cleanup"],
)


@render_statement
@pytest.mark.parametrize("field", ["database", "schema", "table"])
@pytest.mark.parametrize("name", UNSAFE_NAMES)
def test_statements_reject_unsafe_names(
    render: Callable[[TableSlice], str], verb: str, field: str, name: str
) -> None:

    with pytest.raises(DagsterInvariantViolationError, match=re.escape(f"{field} {name!r}")):
        render(table_slice_with(field, name))


@render_statement
@pytest.mark.parametrize(
    ("database", "schema", "table"),
    [
        ("database_abc", "schema1", "table1"),
        ("TESTDB", "TESTSCHEMA", "MY_TABLE"),
        ("_db", "Mixed_Case", "t$1"),
    ],
)
def test_statements_keep_plain_names_unquoted(
    render: Callable[[TableSlice], str], verb: str, database: str, schema: str, table: str
) -> None:
    table_slice = TableSlice(database=database, schema=schema, table=table)

    assert render(table_slice) == f"{verb} FROM {database}.{schema}.{table}"


class RecordingConnection:
    def __init__(self):
        self.statements: list[str] = []

    def cursor(self) -> "RecordingConnection":
        return self

    def __enter__(self) -> "RecordingConnection":
        return self

    def __exit__(self, *args) -> None:
        pass

    def execute(self, statement: str) -> None:
        self.statements.append(statement)

    def fetchall(self) -> list:
        return []


@pytest.mark.parametrize("field", ["database", "schema"])
def test_ensure_schema_exists_rejects_unsafe_names_before_any_statement(field: str) -> None:
    connection = RecordingConnection()

    with pytest.raises(DagsterInvariantViolationError):
        SnowflakeDbClient.ensure_schema_exists(
            build_output_context(), table_slice_with(field, "x' --"), connection
        )

    assert connection.statements == []


def test_ensure_schema_exists_keeps_plain_names() -> None:
    connection = RecordingConnection()

    SnowflakeDbClient.ensure_schema_exists(
        build_output_context(),
        TableSlice(database="TESTDB", schema="TESTSCHEMA", table="MY_TABLE"),
        connection,
    )

    assert connection.statements == [
        "show schemas like 'TESTSCHEMA' in database TESTDB",
        "create schema TESTSCHEMA;",
    ]


class PassTypeHandler(DbTypeHandler[int]):
    def handle_output(self, *args, **kwargs):
        return None

    def load_input(self, *args, **kwargs):
        return None

    @property
    def supported_types(self):
        return [int]


class PassSnowflakeIOManager(SnowflakeIOManager):
    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def type_handlers(self):
        return [PassTypeHandler()]


@asset
def return_one() -> int:
    return 1


def test_run_config_cannot_override_schema_with_unsafe_name() -> None:
    io_manager = PassSnowflakeIOManager(
        account="account", user="user", password="password", database="TESTDB", schema="TESTSCHEMA"
    )

    with mock.patch("snowflake.connector.connect") as connect:
        with pytest.raises(DagsterInvariantViolationError, match="schema"):
            materialize(
                [return_one],
                resources={"io_manager": io_manager},
                run_config={
                    "resources": {
                        "io_manager": {
                            "config": {
                                "account": "account",
                                "user": "user",
                                "database": "TESTDB",
                                "schema": "x; drop table y",
                            }
                        }
                    }
                },
            )

    assert connect.call_count == 0


def test_fetch_last_updated_timestamps_rejects_unsafe_database() -> None:
    connection = RecordingConnection()

    with pytest.raises(DagsterInvariantViolationError, match="database"):
        fetch_last_updated_timestamps(
            snowflake_connection=connection,  # ty: ignore[invalid-argument-type]
            schema="TESTSCHEMA",
            tables=["my_table"],
            database="TESTDB.x; drop table y",
        )

    assert connection.statements == []


@pytest.mark.parametrize(
    "build", [build_information_schema_tables_sql, build_information_schema_columns_sql]
)
def test_information_schema_queries_reject_unsafe_database(
    build: Callable[[str, list[str]], str],
) -> None:
    with pytest.raises(DagsterInvariantViolationError, match="database"):
        build("DB.x; drop table y", ["SCH"])
