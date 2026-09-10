import logging
import random
import re
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

# pyodbc surfaces these through a generic ProgrammingError rather than a dedicated type,
# so they have to be matched on the native error number.
_OBJECT_ALREADY_EXISTS = 2714
_DUPLICATE_INDEX = 1913
_DUPLICATE_OBJECT_ERRNOS = frozenset({_OBJECT_ALREADY_EXISTS, _DUPLICATE_INDEX})

# Errors that retrying cannot fix. Retrying them spends the whole backoff budget and then
# reports "too many retries", so a wrong password reads as a flaky network. Anything not
# listed here is retried, on the grounds that an unrecognized error is more likely
# transient than permanent.
_FATAL_CONNECTION_ERRNOS = frozenset(
    {
        18456,  # login failed for user
        18470,  # login failed: account is disabled
        4062,  # cannot open user default database
        4063,  # cannot open database requested by login
        916,  # server principal cannot access the database under the current security context
        229,  # permission denied on object
        262,  # permission denied (CREATE)
        40615,  # Azure SQL: client IP is not allowed by the server firewall
    }
)

# Errors that are transient by nature. Azure SQL raises most of these routinely during a
# failover, a service reconfiguration, or throttling, and they can take tens of seconds to
# clear, which is why the backoff grows rather than staying flat.
_TRANSIENT_ERRNOS = frozenset(
    {
        0,  # driver-level failure, e.g. "Communication link failure"
        20,  # instance does not support encryption (transient during failover)
        64,  # connection established, then failed during login
        233,  # no process on the other end of the pipe
        1205,  # chosen as the deadlock victim
        4060,  # cannot open the requested database (Azure: still coming online)
        10053,  # transport-level error: connection aborted
        10054,  # transport-level error: connection reset by peer
        10060,  # network error / TCP timeout
        10928,  # Azure: resource ID limit reached
        10929,  # Azure: resource governance minimum guarantee not met
        40143,  # Azure: service encountered an error
        40197,  # Azure: service error during reconfiguration
        40501,  # Azure: service is currently busy (engine throttling)
        40540,  # Azure: service encountered an error
        40613,  # Azure: database is currently unavailable
        42108,  # Azure: instance is waking up
        42109,  # Azure: instance is starting
        49918,  # Azure: not enough resources to process the request
        49919,  # Azure: too many create/update operations in progress
        49920,  # Azure: too many operations in progress
    }
)

_DEADLOCK = 1205

# Cap on the exponential backoff. An Azure failover is usually done inside a minute, so
# waiting longer than this between attempts spends the budget without improving the odds.
DEFAULT_MAX_RETRY_WAIT = 30.0

_ERRNO_PATTERN = re.compile(r"\((\d+)\)")


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
    fn: Callable[[], T],
    retry_limit: int = 5,
    retry_wait: float = 0.2,
    max_retry_wait: float = DEFAULT_MAX_RETRY_WAIT,
) -> T:
    # Retry logic to recover from the case where two processes are creating
    # tables at the same time using sqlalchemy

    check.callable_param(fn, "fn")
    check.int_param(retry_limit, "retry_limit")
    check.numeric_param(retry_wait, "retry_wait")
    check.numeric_param(max_retry_wait, "max_retry_wait")

    attempt = 0
    while True:
        try:
            return fn()
        except (
            db_exc.ProgrammingError,
            db_exc.IntegrityError,
            pyodbc.ProgrammingError,
            pyodbc.IntegrityError,
        ) as exc:
            if _is_duplicate_object_error(exc) or is_fatal_connection_error(exc):
                raise
            if retry_limit == 0:
                raise DagsterMSSQLException("too many retries for DB creation") from exc

            wait = _backoff(retry_wait, attempt, max_retry_wait)
            logging.warning(
                "Retrying failed database creation in %.1fs (%d attempt(s) left): %s",
                wait,
                retry_limit,
                exc,
            )

        time.sleep(wait)
        attempt += 1
        retry_limit -= 1


def error_numbers(exc: BaseException) -> frozenset[int]:
    """The SQL Server native error numbers carried by `exc`.

    pyodbc has no attribute for the native error number: it embeds it in the message, in
    parentheses, alongside other parenthesized text such as the ODBC function name, as in
    ``... There is already an object named 'runs' ... (2714) (SQLExecDirectW)``. So every
    parenthesized integer is collected and callers match against the set. A SQLAlchemy
    wrapper keeps the underlying pyodbc exception on ``.orig``.
    """
    orig = getattr(exc, "orig", None) or exc
    args = getattr(orig, "args", ())
    numbers: set[int] = set()
    for arg in args:
        if isinstance(arg, str):
            numbers.update(int(match) for match in _ERRNO_PATTERN.findall(arg))
    return frozenset(numbers)


def _is_duplicate_object_error(exc: BaseException) -> bool:
    """True if `exc` is SQL Server complaining that the object already exists."""
    return bool(error_numbers(exc) & _DUPLICATE_OBJECT_ERRNOS)


def is_fatal_connection_error(exc: BaseException) -> bool:
    """True if reconnecting cannot possibly succeed: bad credentials, no permission."""
    return bool(error_numbers(exc) & _FATAL_CONNECTION_ERRNOS)


def is_transient_error(exc: BaseException) -> bool:
    """True if `exc` is one of the errors SQL Server and Azure SQL raise in passing."""
    return bool(error_numbers(exc) & _TRANSIENT_ERRNOS)


def _backoff(retry_wait: float, attempt: int, max_retry_wait: float) -> float:
    """Exponential backoff with full jitter.

    Jittered because an Azure failover drops the webserver, the daemon and every code
    location at the same instant. Backing off in lockstep would have them all arrive
    together on a server that is still coming up.
    """
    ceiling = min(retry_wait * (2**attempt), max_retry_wait)
    return random.uniform(0, ceiling)


def retry_mssql_connection_fn(
    fn: Callable[[], T],
    retry_limit: int = 5,
    retry_wait: float = 0.2,
    max_retry_wait: float = DEFAULT_MAX_RETRY_WAIT,
) -> T:
    """Reusable retry logic for any SQL Server connection functions that may fail.

    Intended to be used anywhere we connect to SQL Server, to gracefully handle transient
    connection issues.

    A rejected login, a missing permission or a firewall rule is raised immediately.
    Retrying those would spend the whole budget and then report "too many retries", which
    reads as a network problem and misdirects whoever is debugging it.
    """
    check.callable_param(fn, "fn")
    check.int_param(retry_limit, "retry_limit")
    check.numeric_param(retry_wait, "retry_wait")
    check.numeric_param(max_retry_wait, "max_retry_wait")

    attempt = 0
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
            if is_fatal_connection_error(exc):
                raise

            if retry_limit == 0:
                raise DagsterMSSQLException("too many retries for DB connection") from exc

            wait = _backoff(retry_wait, attempt, max_retry_wait)
            logging.warning(
                "Retrying failed database connection in %.1fs (%d attempt(s) left): %s",
                wait,
                retry_limit,
                exc,
            )

        time.sleep(wait)
        attempt += 1
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
    # tree. The shared tree in dagster core contains per-dialect branches whose DDL is
    # not valid on SQL Server, and its revisions have never been exercised against it.
    return get_alembic_config(
        dunder_file,
        config_path="../alembic/alembic.ini",
        script_location="dagster_mssql:alembic",
    )


def mssql_isolation_level() -> str:
    """The isolation level dagster's SQL Server connections run at.

    Matches Postgres, but only behaves like it once READ_COMMITTED_SNAPSHOT is enabled on
    the database. See `warn_if_read_committed_snapshot_disabled`.
    """
    return "READ COMMITTED"


def is_deadlock_victim(exc: BaseException) -> bool:
    return _DEADLOCK in error_numbers(exc)


def retry_transaction(
    fn: Callable[[], T],
    # Ten rather than five: an attempt costs almost nothing, and giving up drops a write
    # the caller has no way to know was lost. Five is measurably not enough under the
    # contention of several daemons writing heartbeats and asset keys at once.
    retry_limit: int = 10,
    retry_wait: float = 0.05,
    max_retry_wait: float = 2.0,
) -> T:
    """Rerun `fn` when the transaction it runs was lost for a reason that may not recur.

    Two causes, both of which leave the transaction rolled back:

    * Deadlock. Dagster's upserts run under SERIALIZABLE (see ``merge.py``), where SQL
      Server protects a key *range* rather than a row, so concurrent writers are chosen as
      victims even on rows they do not share. SQL Server says what to do about it: "Rerun
      the transaction".
    * A transient failure part-way through, which on Azure SQL Database means a failover,
      a reconfiguration or throttling. `retry_mssql_connection_fn` cannot help here: it
      guards `engine.connect`, and by the time a statement is executing the connection is
      already established.

    `fn` must run the whole transaction rather than a single statement, because that is
    the unit that was rolled back. It must also be safe to run twice -- which holds for a
    single `conn.begin()` block, and does not for a method that opens two of them in
    sequence. ``SqlEventLogStorage.store_event`` is the example: it inserts the event in
    one transaction and the asset rows in another, so retrying the whole thing would
    duplicate the event. That is why only the second half is wrapped.
    """
    check.callable_param(fn, "fn")
    check.int_param(retry_limit, "retry_limit")
    check.numeric_param(retry_wait, "retry_wait")
    check.numeric_param(max_retry_wait, "max_retry_wait")

    attempt = 0
    while True:
        try:
            return fn()
        except (db_exc.DBAPIError, pyodbc.Error) as exc:
            deadlock = is_deadlock_victim(exc)
            if not deadlock and not is_transient_error(exc):
                raise
            if retry_limit == 0:
                cause = "being chosen as the deadlock victim" if deadlock else "a transient error"
                raise DagsterMSSQLException(f"too many retries after {cause}") from exc
            wait = _backoff(retry_wait, attempt, max_retry_wait)
            logging.debug(
                "%s; rerunning the transaction in %.3fs",
                "Deadlock victim" if deadlock else "Transient failure",
                wait,
            )

        time.sleep(wait)
        attempt += 1
        retry_limit -= 1


# Retained under the old name: it only ever handled deadlocks, and now handles transient
# failures too.
retry_on_deadlock = retry_transaction


# Databases already warned about, so that three storage classes sharing one database
# produce one warning rather than three.
_RCSI_WARNED: set[str] = set()

RCSI_WARNING = (
    "READ_COMMITTED_SNAPSHOT is not enabled on SQL Server database '%s'. Under the default"
    " READ COMMITTED isolation SQL Server takes shared read locks, so the dagster daemon"
    " and webserver will block each other under load, which Postgres and MySQL do not do."
    " Enable it with: ALTER DATABASE [%s] SET READ_COMMITTED_SNAPSHOT ON;"
    " (Azure SQL Database has it on by default.)"
)


def warn_if_read_committed_snapshot_disabled(engine: db.engine.Engine) -> bool | None:
    """Warn once per database if row-versioned reads are off.

    Returns True/False for the setting, or None if it could not be determined.

    Enabling it is left to whoever provisions the database: it is a database-wide change
    needing elevated permissions and, briefly, exclusive access, which storage startup
    should not do on a user's behalf. The warning is worth emitting because the symptom
    otherwise is intermittent timeouts under load, a long way from the cause.
    """
    try:
        with engine.connect() as conn:
            row = conn.execute(
                db.text(
                    "SELECT DB_NAME(), is_read_committed_snapshot_on"
                    " FROM sys.databases WHERE database_id = DB_ID()"
                )
            ).first()
    except db_exc.SQLAlchemyError:
        # Reading sys.databases needs no special grant, but a locked-down deployment may
        # still refuse it. Not being able to check is not a reason to fail startup.
        logging.debug("Could not determine READ_COMMITTED_SNAPSHOT state", exc_info=True)
        return None

    if row is None:
        return None

    db_name, enabled = row[0], bool(row[1])
    if not enabled and db_name not in _RCSI_WARNED:
        _RCSI_WARNED.add(db_name)
        logging.warning(RCSI_WARNING, db_name, db_name)
    return enabled


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
