import logging
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import TypeVar
from urllib.parse import (
    quote_plus as urlquote,
    urlparse,
)

import pyodbc
import sqlalchemy as db
import sqlalchemy.exc as db_exc
from alembic.config import Config
from dagster import _check as check
from dagster._core.storage.config import MsSqlStorageConfig
from dagster._core.storage.sql import get_alembic_config
from sqlalchemy.engine import Connection

T = TypeVar("T")

# Escape character for LIKE patterns. T-SQL treats `[` as a metacharacter in addition to
# the standard `%` and `_`, so patterns built from user data need an explicit ESCAPE.
LIKE_ESCAPE_CHAR = "/"

DEFAULT_MSSQL_PORT = 1433
DEFAULT_MSSQL_DRIVER = "ODBC Driver 18 for SQL Server"
DEFAULT_MSSQL_SCHEME = "mssql+pyodbc"

# SQL Server error numbers we treat as "the object already exists", raised when two
# processes race to create the same table.  Unlike MySQL and Postgres, pyodbc surfaces
# these through a generic ProgrammingError, so they have to be matched on the number.
_OBJECT_ALREADY_EXISTS = 2714
_DUPLICATE_INDEX = 1913
_DUPLICATE_OBJECT_ERRNOS = frozenset({_OBJECT_ALREADY_EXISTS, _DUPLICATE_INDEX})


class DagsterMSSQLException(Exception):
    pass


def get_conn(conn_string: str) -> pyodbc.Connection:
    return pyodbc.connect(pyodbc_connection_string(conn_string))


def pyodbc_connection_string(conn_string: str) -> str:
    """Turn a SQLAlchemy URL back into a raw ODBC connection string.

    Used for the connectivity probes that run before any engine exists.
    """
    url = db.engine.make_url(conn_string)
    # a repeated query parameter arrives as a tuple; keep the last occurrence
    query = {k: (v[-1] if isinstance(v, tuple) else v) for k, v in url.query.items()}
    driver = query.pop("driver", DEFAULT_MSSQL_DRIVER)
    parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={url.host},{url.port or DEFAULT_MSSQL_PORT}",
        f"DATABASE={url.database}",
    ]
    if url.username:
        parts.append(f"UID={url.username}")
    if url.password:
        parts.append(f"PWD={url.password}")
    parts.extend(f"{k}={v}" for k, v in query.items())
    return ";".join(parts)


def mssql_url_from_config(config_value: MsSqlStorageConfig) -> str:
    if config_value.get("mssql_url"):
        return config_value["mssql_url"]

    return get_conn_string(**config_value["mssql_db"])


def get_conn_string(
    username: str,
    password: str,
    hostname: str,
    db_name: str,
    port: int | str = DEFAULT_MSSQL_PORT,
    driver: str = DEFAULT_MSSQL_DRIVER,
    params: dict[str, object] | None = None,
    scheme: str = DEFAULT_MSSQL_SCHEME,
) -> str:
    # pyodbc selects a locally installed ODBC driver by name, so it is always part of the
    # URL; anything else (Encrypt, TrustServerCertificate, Authentication for Entra ID)
    # rides along as a query parameter.
    query = {"driver": driver, **(params or {})}
    query_string = "&".join(f"{k}={urlquote(str(v))}" for k, v in query.items())

    return (
        f"{scheme}://{urlquote(username)}:{urlquote(password)}@{hostname}:{port}/{db_name}"
        f"?{query_string}"
    )


def parse_mssql_version(version: str) -> tuple[int, ...]:
    """Parse a SQL Server version into a tuple of ints.

    ``SELECT @@VERSION`` returns a banner rather than a bare version, so the numeric
    version is read from ``SERVERPROPERTY('ProductVersion')`` instead, which looks like
    ``16.0.4265.3``.
    """
    parsed = []
    for part in version.split("."):
        try:
            parsed.append(int(part.strip()))
        except ValueError:
            break
    return tuple(parsed)


def retry_mssql_creation_fn(
    fn: Callable[[], T], retry_limit: int = 5, retry_wait: float = 0.2
) -> T:
    # Retry logic to recover from the case where two processes are creating
    # tables at the same time using sqlalchemy

    check.callable_param(fn, "fn")
    check.int_param(retry_limit, "retry_limit")
    check.numeric_param(retry_wait, "retry_wait")

    while True:
        try:
            return fn()
        except (
            db_exc.ProgrammingError,
            db_exc.IntegrityError,
            pyodbc.ProgrammingError,
            pyodbc.IntegrityError,
        ) as exc:
            if _is_duplicate_object_error(exc):
                raise
            logging.warning("Retrying failed database creation")
            if retry_limit == 0:
                raise DagsterMSSQLException("too many retries for DB creation") from exc

        time.sleep(retry_wait)
        retry_limit -= 1


def _is_duplicate_object_error(exc: BaseException) -> bool:
    """True if `exc` is SQL Server complaining that the object already exists.

    pyodbc reports the native error number as the second element of ``exc.args``; a
    SQLAlchemy wrapper keeps the underlying exception on ``.orig``.
    """
    orig = getattr(exc, "orig", None) or exc
    args = getattr(orig, "args", ())
    if len(args) >= 2 and isinstance(args[1], str):
        return any(f"({errno})" in args[1] for errno in _DUPLICATE_OBJECT_ERRNOS)
    return False


def retry_mssql_connection_fn(
    fn: Callable[[], T],
    retry_limit: int = 5,
    retry_wait: float = 0.2,
) -> T:
    """Reusable retry logic for any SQL Server connection functions that may fail.
    Intended to be used anywhere we connect to SQL Server, to gracefully handle transient
    connection issues.
    """
    check.callable_param(fn, "fn")
    check.int_param(retry_limit, "retry_limit")
    check.numeric_param(retry_wait, "retry_wait")

    while True:
        try:
            return fn()

        except (
            db_exc.DatabaseError,
            db_exc.OperationalError,
            pyodbc.DatabaseError,
            pyodbc.OperationalError,
            pyodbc.InterfaceError,
        ) as exc:
            logging.warning("Retrying failed database connection")
            if retry_limit == 0:
                raise DagsterMSSQLException("too many retries for DB connection") from exc

        time.sleep(retry_wait)
        retry_limit -= 1


def wait_for_connection(conn_string: str, retry_limit: int = 5, retry_wait: float = 0.2) -> bool:
    parsed = urlparse(conn_string)
    check.invariant(parsed.hostname, "conn_string must include a hostname")
    retry_mssql_connection_fn(
        lambda: get_conn(conn_string),
        retry_limit=retry_limit,
        retry_wait=retry_wait,
    )
    return True


def mssql_alembic_config(dunder_file: str) -> Config:
    # Unlike dagster-mysql and dagster-postgres, dagster-mssql ships its own revision
    # tree.  The shared tree in dagster core contains per-dialect branches whose DDL is
    # not valid on SQL Server, and its revisions have never been exercised against it.
    return get_alembic_config(
        dunder_file,
        config_path="../alembic/alembic.ini",
        script_location="dagster_mssql:alembic",
    )


def mssql_isolation_level() -> str:
    """The isolation level dagster's SQL Server connections run at.

    READ COMMITTED matches what Postgres uses.  Note that on SQL Server it takes shared
    read locks by default, so dagster's daemons and the webserver will block each other
    under load.  Enabling READ_COMMITTED_SNAPSHOT on the database gives the row-versioned,
    non-blocking behaviour Postgres has natively::

        ALTER DATABASE <db> SET READ_COMMITTED_SNAPSHOT ON;

    That is deliberately left to whoever provisions the database rather than done here: it
    is a database-wide change, it needs elevated permissions, and it briefly requires
    exclusive access.
    """
    return "READ COMMITTED"


@contextmanager
def create_mssql_connection(
    engine: db.engine.Engine, dunder_file: str, storage_type_desc: str | None = None
) -> Iterator[Connection]:
    check.inst_param(engine, "engine", db.engine.Engine)
    check.str_param(dunder_file, "dunder_file")
    check.opt_str_param(storage_type_desc, "storage_type_desc", "")

    if storage_type_desc:
        storage_type_desc += " "
    else:
        storage_type_desc = ""

    conn_cm = retry_mssql_connection_fn(engine.connect)
    with conn_cm as conn:
        with conn.begin():
            yield conn
