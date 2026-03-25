from collections.abc import Iterable, Iterator, Sequence
from contextlib import contextmanager
from typing import Any

import sqlalchemy as db
from sqlalchemy.engine import Connection

IS_SQLALCHEMY_VERSION_1 = db.__version__.startswith("1.")


def db_select(items: Iterable):
    """Utility class that allows compatability between SqlAlchemy 1.3.x, 1.4.x, and 2.x."""
    if not IS_SQLALCHEMY_VERSION_1:
        return db.select(*items)

    return db.select(items)


def db_case(items: Iterable, else_: Any | None = None):
    """Utility class that allows compatability between SqlAlchemy 1.3.x, 1.4.x, and 2.x."""
    if not IS_SQLALCHEMY_VERSION_1:
        return db.case(*items, else_=else_)

    return db.case(items, else_=else_)


def db_subquery(query, name: str = "subquery"):
    """Utility class that allows compatibility between SqlAlchemy 1.3.x, 1.4.x, and 2.x."""
    if not IS_SQLALCHEMY_VERSION_1:
        return query.subquery(name)

    return query.alias(name)


def db_fetch_mappings(conn: Connection, query: Any) -> Sequence[Any]:
    """Utility class that allows compatibility between SqlAlchemy 1.3.x, 1.4.x, and 2.x."""
    with db_result(conn, query) as result:
        if not IS_SQLALCHEMY_VERSION_1:
            return result.mappings().all()
        return result.fetchall()


@contextmanager
def db_result(conn: Connection, query: Any) -> Iterator[Any]:
    """Context manager that ensures a CursorResult is closed after use.

    In SQLAlchemy 2.x, CursorResult is natively a context manager, but in 1.x
    ResultProxy is not. This shim provides uniform cleanup across both versions,
    preventing connection pool exhaustion when Python's garbage collector delays
    cleanup of CursorResult reference cycles (particularly on Python 3.14+).

    Usage::

        with db_result(conn, query) as result:
            row = result.fetchone()
    """
    if IS_SQLALCHEMY_VERSION_1:
        result = conn.execute(query)
        try:
            yield result
        finally:
            result.close()
    else:
        with conn.execute(query) as result:  # type: ignore (bad stubs)
            yield result


def db_scalar_subquery(query):
    """Utility class that allows compatability between SqlAlchemy 1.3.x, 1.4.x, and 2.x."""
    if not IS_SQLALCHEMY_VERSION_1:
        return query.scalar_subquery()

    return query.as_scalar()
