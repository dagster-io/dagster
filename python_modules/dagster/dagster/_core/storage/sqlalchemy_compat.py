from typing import Any, Iterable, Optional, Sequence

import sqlalchemy as db

IS_SQLALCHEMY_VERSION_1 = db.__version__.startswith("1.")


def db_select(items: Iterable):
    """Utility class that allows compatability between SqlAlchemy 1.3.x, 1.4.x, and 2.x."""
    if not IS_SQLALCHEMY_VERSION_1:
        return db.select(*items)

    return db.select(items)


def db_case(items: Iterable, else_: Optional[Any] = None):
    """Utility class that allows compatability between SqlAlchemy 1.3.x, 1.4.x, and 2.x."""
    if not IS_SQLALCHEMY_VERSION_1:
        return db.case(*items, else_=else_)

    return db.case(items, else_=else_)


def db_subquery(query, name: str = "subquery"):
    """Utility class that allows compatibility between SqlAlchemy 1.3.x, 1.4.x, and 2.x."""
    if not IS_SQLALCHEMY_VERSION_1:
        return query.subquery(name)

    return query.alias(name)


def db_fetch_mappings(conn, query: Any) -> Sequence[Any]:
    """Utility class that allows compatibility between SqlAlchemy 1.3.x, 1.4.x, and 2.x."""
    if not IS_SQLALCHEMY_VERSION_1:
        return conn.execute(query).mappings().all()

    return conn.execute(query).fetchall()


def db_scalar_subquery(query):
    """Utility class that allows compatability between SqlAlchemy 1.3.x, 1.4.x, and 2.x."""
    if not IS_SQLALCHEMY_VERSION_1:
        return query.scalar_subquery()

    return query.as_scalar()
