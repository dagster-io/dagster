import logging
import time
from contextlib import contextmanager
from urllib.parse import quote_plus as urlquote

import psycopg2
import psycopg2.errorcodes
import sqlalchemy
from dagster import Field, IntSource, Selector, StringSource, check
from dagster.core.storage.sql import get_alembic_config, handle_schema_errors


class DagsterPostgresException(Exception):
    pass


def get_conn(conn_string):
    conn = psycopg2.connect(conn_string)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    return conn


def pg_config():
    return Selector(
        {
            "postgres_url": str,
            "postgres_db": {
                "username": StringSource,
                "password": StringSource,
                "hostname": StringSource,
                "db_name": StringSource,
                "port": Field(IntSource, is_required=False, default_value=5432),
            },
        }
    )


def pg_url_from_config(config_value):
    if config_value.get("postgres_url"):
        return config_value["postgres_url"]

    return get_conn_string(**config_value["postgres_db"])


def get_conn_string(username, password, hostname, db_name, port="5432"):
    return "postgresql://{username}:{password}@{hostname}:{port}/{db_name}".format(
        username=username,
        password=urlquote(password),
        hostname=hostname,
        db_name=db_name,
        port=port,
    )


def retry_pg_creation_fn(fn, retry_limit=5, retry_wait=0.2):
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


def retry_pg_connection_fn(fn, retry_limit=5, retry_wait=0.2):
    """Reusable retry logic for any psycopg2/sqlalchemy PG connection functions that may fail.
    Intended to be used anywhere we connect to PG, to gracefully handle transient connection issues.
    """
    check.callable_param(fn, "fn")
    check.int_param(retry_limit, "retry_limit")
    check.numeric_param(retry_wait, "retry_wait")

    while True:
        try:
            return fn()
        except (
            # See: https://www.psycopg.org/docs/errors.html
            # These are broad, we may want to list out specific exceptions to capture
            psycopg2.DatabaseError,
            psycopg2.OperationalError,
            sqlalchemy.exc.DatabaseError,
            sqlalchemy.exc.OperationalError,
        ) as exc:
            logging.warning("Retrying failed database connection")
            if retry_limit == 0:
                raise DagsterPostgresException("too many retries for DB connection") from exc

        time.sleep(retry_wait)
        retry_limit -= 1


def wait_for_connection(conn_string, retry_limit=5, retry_wait=0.2):
    retry_pg_connection_fn(
        lambda: psycopg2.connect(conn_string), retry_limit=retry_limit, retry_wait=retry_wait
    )
    return True


@contextmanager
def create_pg_connection(engine, dunder_file, storage_type_desc=None):
    check.inst_param(engine, "engine", sqlalchemy.engine.Engine)
    check.str_param(dunder_file, "dunder_file")
    check.opt_str_param(storage_type_desc, "storage_type_desc", "")

    if storage_type_desc:
        storage_type_desc += " "
    else:
        storage_type_desc = ""

    conn = None
    try:
        # Retry connection to gracefully handle transient connection issues
        conn = retry_pg_connection_fn(engine.connect)
        with handle_schema_errors(
            conn,
            get_alembic_config(dunder_file),
            msg="Postgres {}storage requires migration".format(storage_type_desc),
        ):
            yield conn
    finally:
        if conn:
            conn.close()


def pg_statement_timeout(millis):
    check.int_param(millis, "millis")
    return "-c statement_timeout={}".format(millis)
