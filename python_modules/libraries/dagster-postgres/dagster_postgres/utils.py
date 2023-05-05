import logging
import time
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Mapping, Optional, TypeVar
from urllib.parse import quote, urlencode

import alembic.config
import psycopg2
import psycopg2.errorcodes
import psycopg2.extensions
import sqlalchemy
import sqlalchemy.exc
from dagster import _check as check
from dagster._core.definitions.policy import Backoff, Jitter, calculate_delay

# re-export
from dagster._core.storage.config import pg_config as pg_config
from dagster._core.storage.event_log.sql_event_log import SqlDbConnection
from dagster._core.storage.sql import get_alembic_config
from sqlalchemy.engine import Connection

T = TypeVar("T")


class DagsterPostgresException(Exception):
    pass


def get_conn(conn_string: str) -> SqlDbConnection:
    """Get a connection directly without SQLAlchemy for tests."""
    conn = psycopg2.connect(conn_string)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    return conn


def pg_url_from_config(config_value: Mapping[str, Any]) -> str:
    if config_value.get("postgres_url"):
        check.invariant(
            "postgres_db" not in config_value,
            "postgres storage config must have exactly one of `postgres_url` or `postgres_db`",
        )
        return config_value["postgres_url"]
    else:
        check.invariant(
            "postgres_db" in config_value,
            "postgres storage config must have exactly one of `postgres_url` or `postgres_db`",
        )

        return get_conn_string(**config_value["postgres_db"])


def get_conn_string(
    username: str,
    password: str,
    hostname: str,
    db_name: str,
    port: str = "5432",
    params: Optional[Mapping[str, object]] = None,
    scheme: str = "postgresql",
) -> str:
    uri = f"{scheme}://{quote(username)}:{quote(password)}@{hostname}:{port}/{db_name}"

    if params:
        query_string = f"{urlencode(params, quote_via=quote)}"
        uri = f"{uri}?{query_string}"

    return uri


def retry_pg_creation_fn(fn: Callable[[], T], retry_limit: int = 5, retry_wait: float = 0.2) -> T:
    # Retry logic to recover from the case where two processes are creating
    # tables at the same time using sqlalchemy

    check.callable_param(fn, "fn")
    check.int_param(retry_limit, "retry_limit")
    check.numeric_param(retry_wait, "retry_wait")

    while True:
        try:
            return fn()
        except (
            psycopg2.ProgrammingError,
            psycopg2.IntegrityError,
            sqlalchemy.exc.ProgrammingError,
            sqlalchemy.exc.IntegrityError,
        ) as exc:
            # Only programming error we want to retry on is the DuplicateTable error
            if (
                isinstance(exc, sqlalchemy.exc.ProgrammingError)
                and exc.orig
                and exc.orig.pgcode != psycopg2.errorcodes.DUPLICATE_TABLE
            ) or (
                isinstance(exc, psycopg2.ProgrammingError)
                and exc.pgcode != psycopg2.errorcodes.DUPLICATE_TABLE
            ):
                raise

            logging.warning("Retrying failed database creation")
            if retry_limit == 0:
                raise DagsterPostgresException("too many retries for DB creation") from exc

        time.sleep(retry_wait)
        retry_limit -= 1


def retry_pg_connection_fn(fn: Callable[[], T], retry_limit: int = 5, retry_wait: float = 0.2) -> T:
    """Reusable retry logic for any psycopg2/sqlalchemy PG connection functions that may fail.
    Intended to be used anywhere we connect to PG, to gracefully handle transient connection issues.
    """
    check.callable_param(fn, "fn")
    check.int_param(retry_limit, "retry_limit")
    check.numeric_param(retry_wait, "retry_wait")
    attempt_num = 0
    while True:
        attempt_num += 1
        try:
            return fn()
        except (
            # See: https://www.psycopg.org/docs/errors.html
            # These are broad, we may want to list out specific exceptions to capture
            psycopg2.DatabaseError,
            psycopg2.OperationalError,
            sqlalchemy.exc.DatabaseError,
            sqlalchemy.exc.OperationalError,
            sqlalchemy.exc.TimeoutError,
        ) as exc:
            logging.warning("Retrying failed database connection: %s", exc)
            if attempt_num > retry_limit:
                raise DagsterPostgresException("too many retries for DB connection") from exc

        time.sleep(
            calculate_delay(
                attempt_num=attempt_num,
                base_delay=retry_wait,
                jitter=Jitter.PLUS_MINUS,
                backoff=Backoff.EXPONENTIAL,
            )
        )


def wait_for_connection(conn_string: str, retry_limit: int = 5, retry_wait: float = 0.2) -> bool:
    """Get a connection with retries directly without SQLAlchemy for tests."""
    retry_pg_connection_fn(
        lambda: psycopg2.connect(conn_string), retry_limit=retry_limit, retry_wait=retry_wait
    )
    return True


def pg_alembic_config(
    dunder_file: str, script_location: Optional[str] = None
) -> alembic.config.Config:
    return get_alembic_config(
        dunder_file, config_path="../alembic/alembic.ini", script_location=script_location
    )


@contextmanager
def create_pg_connection(
    engine: sqlalchemy.engine.Engine,
) -> Iterator[Connection]:
    check.inst_param(engine, "engine", sqlalchemy.engine.Engine)
    conn = None
    try:
        # Retry connection to gracefully handle transient connection issues
        conn = retry_pg_connection_fn(engine.connect)
        yield conn
    finally:
        if conn:
            conn.close()


def pg_statement_timeout(millis: int) -> str:
    check.int_param(millis, "millis")
    return f"-c statement_timeout={millis}"
