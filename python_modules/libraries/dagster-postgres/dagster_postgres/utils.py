import logging
import time
from contextlib import contextmanager
from urllib.parse import quote, urlencode

import psycopg2
import psycopg2.errorcodes
import sqlalchemy

from dagster import Field, IntSource, Permissive, StringSource
from dagster import _check as check
from dagster.core.definitions.policy import Backoff, Jitter, calculate_delay
from dagster.core.storage.sql import get_alembic_config


class DagsterPostgresException(Exception):
    pass


def get_conn(conn_string):
    conn = psycopg2.connect(conn_string)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    return conn


def pg_config():
    return {
        "postgres_url": Field(StringSource, is_required=False),
        "postgres_db": Field(
            {
                "username": StringSource,
                "password": StringSource,
                "hostname": StringSource,
                "db_name": StringSource,
                "port": Field(IntSource, is_required=False, default_value=5432),
                "params": Field(Permissive(), is_required=False, default_value={}),
            },
            is_required=False,
        ),
        "should_autocreate_tables": Field(bool, is_required=False, default_value=True),
    }


def pg_url_from_config(config_value):

    if config_value.get("postgres_url"):
        check.invariant(
            not "postgres_db" in config_value,
            "postgres storage config must have exactly one of `postgres_url` or `postgres_db`",
        )
        return config_value["postgres_url"]
    else:
        check.invariant(
            "postgres_db" in config_value,
            "postgres storage config must have exactly one of `postgres_url` or `postgres_db`",
        )

        return get_conn_string(**config_value["postgres_db"])


def get_conn_string(username, password, hostname, db_name, port="5432", params=None):
    uri = f"postgresql://{quote(username)}:{quote(password)}@{hostname}:{port}/{db_name}"

    if params:
        query_string = f"{urlencode(params, quote_via=quote)}"
        uri = f"{uri}?{query_string}"

    return uri


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
    """
    Reusable retry logic for any psycopg2/sqlalchemy PG connection functions that may fail.
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


def wait_for_connection(conn_string, retry_limit=5, retry_wait=0.2):
    retry_pg_connection_fn(
        lambda: psycopg2.connect(conn_string), retry_limit=retry_limit, retry_wait=retry_wait
    )
    return True


def pg_alembic_config(dunder_file, script_location=None):
    return get_alembic_config(
        dunder_file, config_path="../alembic/alembic.ini", script_location=script_location
    )


@contextmanager
def create_pg_connection(engine, _alembic_config, storage_type_desc=None):
    check.inst_param(engine, "engine", sqlalchemy.engine.Engine)
    check.opt_str_param(storage_type_desc, "storage_type_desc", "")

    if storage_type_desc:
        storage_type_desc += " "
    else:
        storage_type_desc = ""

    conn = None
    try:
        # Retry connection to gracefully handle transient connection issues
        conn = retry_pg_connection_fn(engine.connect)
        yield conn
    finally:
        if conn:
            conn.close()


def pg_statement_timeout(millis):
    check.int_param(millis, "millis")
    return "-c statement_timeout={}".format(millis)
