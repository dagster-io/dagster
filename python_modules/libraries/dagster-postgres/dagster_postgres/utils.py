import importlib
import logging
import time
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from typing import Any, TypeVar
from urllib.parse import quote, urlencode

import alembic.config
import sqlalchemy
import sqlalchemy.exc
from dagster import _check as check
from dagster._core.definitions.policy import Backoff, Jitter, calculate_delay
from dagster._core.errors import DagsterInvariantViolationError

# re-export
from dagster._core.storage.config import pg_config as pg_config
from dagster._core.storage.sql import get_alembic_config
from sqlalchemy.engine import Connection

T = TypeVar("T")


class DagsterPostgresException(Exception):
    pass


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


def pg_config_password_provider(config_value: Mapping[str, Any]) -> str | None:
    if config_value.get("postgres_db"):
        return config_value["postgres_db"].get("password_provider")
    return None


def get_conn_string(
    username: str,
    password: str | None = None,
    hostname: str = "",
    db_name: str = "",
    port: str = "5432",
    params: Mapping[str, object] | None = None,
    scheme: str = "postgresql",
    *,
    password_provider: str | None = None,
) -> str:
    has_password = password is not None
    has_password_provider = password_provider is not None
    check.invariant(
        has_password ^ has_password_provider,
        "postgres storage config must provide exactly one of `password` or `password_provider`",
    )

    pwd_str = password if password is not None else ""
    uri = f"{scheme}://{quote(username)}:{quote(pwd_str)}@{hostname}:{port}/{db_name}"

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
            sqlalchemy.exc.ProgrammingError,
            sqlalchemy.exc.IntegrityError,
        ) as exc:
            # Only programming error we want to retry on is the DuplicateTable error
            if (
                isinstance(exc, sqlalchemy.exc.ProgrammingError)
                and exc.orig
                and exc.orig.pgcode != "42P07"
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
    """Check that we can connect to the PostgreSQL server with retries."""
    retry_pg_connection_fn(
        lambda: sqlalchemy.create_engine(conn_string).connect().close(),
        retry_limit=retry_limit,
        retry_wait=retry_wait,
    )
    return True


def pg_alembic_config(
    dunder_file: str, script_location: str | None = None
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


def set_pg_statement_timeout(conn: Any, millis: int):
    check.int_param(millis, "millis")
    with conn:
        with conn.cursor() as curs:
            curs.execute(f"SET statement_timeout = {millis};")


def setup_pg_password_provider_event(
    engine: sqlalchemy.engine.Engine, password_provider: str
) -> None:
    """
    Sets up an SQLAlchemy do_connect event listener that dynamically retrieves the password
    by importing and invoking the callable specified by `password_provider`.
    
    The callable returns a string password/token to be injected into the connection params.
    
    WARNING: `password_provider` is dynamically imported using `importlib.import_module`.
             This should only be used with trusted code paths.
    """
    parts = password_provider.split(".")
    if len(parts) < 2:
        raise DagsterInvariantViolationError(
            f"password_provider must be a dot-separated string like 'my_module.my_function'. "
            f"Got: '{password_provider}'"
        )
    module_name = ".".join(parts[:-1])
    callable_name = parts[-1]

    try:
        module = importlib.import_module(module_name)
    except ImportError as e:
        raise DagsterInvariantViolationError(
            f"Could not import module '{module_name}' specified in password_provider: {e}"
        ) from e

    try:
        get_password = getattr(module, callable_name)
    except AttributeError as e:
        raise DagsterInvariantViolationError(
            f"Could not find callable '{callable_name}' in module '{module_name}'"
        ) from e

    check.callable_param(get_password, "password_provider")

    @sqlalchemy.event.listens_for(engine, "do_connect")
    def receive_do_connect(dialect, conn_rec, cargs, cparams):
        try:
            password = get_password()
        except Exception as e:
            raise DagsterInvariantViolationError(
                f"password_provider '{password_provider}' raised an error while "
                f"fetching credentials: {e}"
            ) from e
        if not isinstance(password, str):
            raise DagsterInvariantViolationError(
                f"password_provider '{password_provider}' must return a str, "
                f"got {type(password).__name__}"
            )
        cparams["password"] = password
