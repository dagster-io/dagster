import re
from collections.abc import Callable

import pytest
from dagster import DagsterInvariantViolationError
from dagster._core.storage.db_io_manager import TableSlice
from dagster_duckdb.io_manager import DuckDbClient, _get_cleanup_statement

UNSAFE_NAMES = ["t; drop table x", "t --", "t'", 't"', "my table", "t()", "1t", "t$"]


def table_slice_with(field: str, name: str) -> TableSlice:
    names = {"schema": "schema1", "table": "table1", field: name}
    return TableSlice(schema=names["schema"], table=names["table"])


render_statement = pytest.mark.parametrize(
    ("render", "verb"),
    [(DuckDbClient.get_select_statement, "SELECT *"), (_get_cleanup_statement, "DELETE")],
    ids=["select", "cleanup"],
)


@render_statement
@pytest.mark.parametrize("field", ["schema", "table"])
@pytest.mark.parametrize("name", UNSAFE_NAMES)
def test_statements_reject_unsafe_names(
    render: Callable[[TableSlice], str], verb: str, field: str, name: str
) -> None:
    table_slice = table_slice_with(field, name)

    with pytest.raises(DagsterInvariantViolationError, match=re.escape(f"{field} {name!r}")):
        render(table_slice)


@render_statement
@pytest.mark.parametrize(
    ("schema", "table"),
    [
        ("schema1", "table1"),
        ("my_schema", "b_df"),
        ("_private", "Table_2"),
        ("public", "café"),
        ("attached_db.analytics", "table1"),
    ],
)
def test_statements_keep_plain_names_unquoted(
    render: Callable[[TableSlice], str], verb: str, schema: str, table: str
) -> None:
    assert render(TableSlice(schema=schema, table=table)) == f"{verb} FROM {schema}.{table}"


@render_statement
@pytest.mark.parametrize(
    ("field", "name"),
    [("schema", "a.b.c"), ("schema", "a."), ("schema", ".a"), ("table", "a.b")],
)
def test_statements_reject_extra_dotted_parts(
    render: Callable[[TableSlice], str], verb: str, field: str, name: str
) -> None:
    with pytest.raises(DagsterInvariantViolationError, match=re.escape(f"{field} {name!r}")):
        render(table_slice_with(field, name))
