"""Upsert support for SQL Server.

SQL Server has no ``INSERT .. ON CONFLICT DO UPDATE`` (Postgres) or ``INSERT .. ON
DUPLICATE KEY UPDATE`` (MySQL). The equivalent is ``MERGE``, which this module builds.

Three details matter and are easy to get wrong:

* ``WITH (HOLDLOCK, UPDLOCK)`` is not optional, and neither hint works alone. Without
  ``HOLDLOCK`` two sessions can both fail to match and both insert, violating the unique
  key. With it but not ``UPDLOCK`` they instead both take a *shared* range lock to probe,
  both try to convert it to exclusive to write, and SQL Server kills one with error 1205.
  ``UPDLOCK`` makes the probe take an update lock, so the second session waits there.
* Rows are sorted by their match key. A multi-row ``MERGE`` locks in row order, and
  callers build rows from dicts whose iteration order they did not choose, so without this
  two callers passing the same keys in different orders deadlock.
* Every parameter is bound with the type of the column it targets. Dagster's text columns
  are ``NVARCHAR`` here, and binding a value as ``VARCHAR`` would round-trip it through
  the database codepage and mangle anything outside it.

Deadlocks remain possible even so, because a range lock covers rows the statement never
touches; ``retry_on_deadlock`` in ``utils.py`` is what makes that survivable.
"""

from collections.abc import Mapping, Sequence
from typing import Any

import sqlalchemy as db


def _quote(identifier: str) -> str:
    escaped = identifier.replace("]", "]]")
    return f"[{escaped}]"


def merge_statement(
    table: db.Table,
    match_on: Sequence[str],
    values: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    update_values: Mapping[str, Any] | None = None,
) -> db.TextClause:
    """Build a MERGE that inserts `values`, or updates the row already matching `match_on`.

    Args:
        table: the target table.
        match_on: column names identifying an existing row, normally the columns covered
            by the unique constraint the upsert is racing on.
        values: a row, or rows, to insert. Every row must have the same columns.
        update_values: what to write when the row already exists, if it differs from
            `values`. Defaults to every column in `values` except those in `match_on`.

    Returns:
        An executable statement with all parameters already bound.
    """
    rows = [values] if isinstance(values, Mapping) else list(values)
    if not rows:
        raise ValueError("merge_statement() requires at least one row")

    columns = list(rows[0].keys())
    if any(set(row.keys()) != set(columns) for row in rows):
        raise ValueError("every row passed to merge_statement() must have the same columns")

    missing = [c for c in match_on if c not in columns]
    if missing:
        raise ValueError(f"match_on columns {missing} are not present in the merged values")

    # Impose a total order on the rows so concurrent callers acquire their range locks in
    # the same sequence and cannot deadlock against each other. Sorting on the string
    # form rather than the values keeps it total across mixed and None-valued keys; the
    # order only has to be consistent, not meaningful.
    if len(rows) > 1:
        rows.sort(key=lambda row: tuple(str(row[c]) for c in match_on))

    bindparams: list[db.BindParameter] = []

    # Bind parameters are named positionally rather than after the column, because a
    # column name is not necessarily a legal bind parameter name.
    def bind(name: str, column: str, value: Any) -> str:
        bindparams.append(db.bindparam(name, value, type_=table.c[column].type))
        return f":{name}"

    source_rows = [
        "({})".format(", ".join(bind(f"src_{i}_{j}", c, row[c]) for j, c in enumerate(columns)))
        for i, row in enumerate(rows)
    ]

    statement = [
        f"MERGE {_quote(table.name)} WITH (HOLDLOCK, UPDLOCK) AS target",
        "USING (VALUES {}) AS source ({})".format(
            ", ".join(source_rows), ", ".join(_quote(c) for c in columns)
        ),
        "ON {}".format(" AND ".join(f"target.{_quote(c)} = source.{_quote(c)}" for c in match_on)),
    ]

    if update_values is None:
        assignments = [f"{_quote(c)} = source.{_quote(c)}" for c in columns if c not in match_on]
    else:
        assignments = [
            f"{_quote(c)} = {bind(f'upd_{j}', c, v)}"
            for j, (c, v) in enumerate(update_values.items())
        ]

    if assignments:
        statement.append(f"WHEN MATCHED THEN UPDATE SET {', '.join(assignments)}")

    statement.append(
        "WHEN NOT MATCHED THEN INSERT ({}) VALUES ({});".format(
            ", ".join(_quote(c) for c in columns),
            ", ".join(f"source.{_quote(c)}" for c in columns),
        )
    )

    return db.text("\n".join(statement)).bindparams(*bindparams)
