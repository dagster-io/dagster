import re
from collections.abc import Callable
from datetime import datetime
from types import SimpleNamespace

import pytest
from dagster import DagsterInvariantViolationError, build_output_context
from dagster._core.storage.db_io_manager import TableSlice
from dagster_gcp import fetch_last_updated_timestamps
from dagster_gcp.bigquery.io_manager import BigQueryClient, _get_cleanup_statement

UNSAFE_NAMES = ["t; drop table x", "t --", "t'", "t`", "my table", "t()", "t\\"]


def table_slice_with(field: str, name: str) -> TableSlice:
    names = {"database": "my-project", "schema": "my_dataset", "table": "my_table", field: name}
    return TableSlice(database=names["database"], schema=names["schema"], table=names["table"])


render_statement = pytest.mark.parametrize(
    ("render", "verb"),
    [
        (BigQueryClient.get_select_statement, "SELECT * FROM"),
        (_get_cleanup_statement, "TRUNCATE TABLE"),
    ],
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
        ("db", "schema1", "table1"),
        ("my-project", "my_dataset", "my-table"),
        ("example.com:my-project", "Dataset_1", "café"),
    ],
)
def test_statements_keep_names_as_before(
    render: Callable[[TableSlice], str], verb: str, database: str, schema: str, table: str
) -> None:
    table_slice = TableSlice(database=database, schema=schema, table=table)

    assert render(table_slice) == f"{verb} `{database}.{schema}.{table}`"


class RecordingConnection:
    def __init__(self):
        self.statements: list[str] = []

    def query(self, statement: str, job_config=None) -> SimpleNamespace:
        self.statements.append(statement)
        row = SimpleNamespace(table_id="my_table", last_modified_time=datetime(2024, 1, 1))
        return SimpleNamespace(result=lambda: [row])


@pytest.mark.parametrize("schema", ["my-dataset", "x; drop table y", "x --"])
def test_ensure_schema_exists_rejects_unsafe_schema(schema: str) -> None:
    connection = RecordingConnection()
    table_slice = TableSlice(database="my-project", schema=schema, table="my_table")

    with pytest.raises(DagsterInvariantViolationError, match="schema"):
        BigQueryClient.ensure_schema_exists(build_output_context(), table_slice, connection)

    assert connection.statements == []


@pytest.mark.parametrize("field", ["database", "schema", "table"])
@pytest.mark.parametrize("write_mode", ["truncate", "replace"])
def test_delete_table_slice_rejects_unsafe_names(field: str, write_mode: str) -> None:
    connection = RecordingConnection()
    context = SimpleNamespace(resource_config={"write_mode": write_mode})

    with pytest.raises(DagsterInvariantViolationError, match=field):
        BigQueryClient.delete_table_slice(
            context,  # ty: ignore[invalid-argument-type]
            table_slice_with(field, "x`"),
            connection,
        )

    assert connection.statements == []


@pytest.mark.parametrize(
    "dataset_id",
    [
        "x; drop table y",
        "x --",
        "my--project.x",
        "`x`",
        "a.b.c",
        "`a`b`.x",
        "`a\\`.x",
        "`a b`.x",
    ],
)
def test_fetch_last_updated_timestamps_rejects_unsafe_dataset(dataset_id: str) -> None:
    connection = RecordingConnection()

    with pytest.raises(DagsterInvariantViolationError, match="dataset_id"):
        fetch_last_updated_timestamps(
            client=connection,  # ty: ignore[invalid-argument-type]
            dataset_id=dataset_id,
            table_ids=["my_table"],
        )

    assert connection.statements == []


@pytest.mark.parametrize(
    "dataset_id",
    [
        "my_dataset",
        "my-project.my_dataset",
        "`my-project`.my_dataset",
        "`example.com:my-project`.my_dataset",
    ],
)
def test_fetch_last_updated_timestamps_keeps_dataset_unquoted(dataset_id: str) -> None:
    connection = RecordingConnection()

    fetch_last_updated_timestamps(
        client=connection,  # ty: ignore[invalid-argument-type]
        dataset_id=dataset_id,
        table_ids=["my_table"],
    )

    assert f"FROM\n            {dataset_id}.__TABLES__" in connection.statements[0]
