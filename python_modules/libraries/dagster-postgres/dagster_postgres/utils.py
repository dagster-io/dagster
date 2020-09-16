import logging
import time
from contextlib import contextmanager

import psycopg2
import six
import sqlalchemy

from dagster import Field, IntSource, Selector, StringSource, check
from dagster.core.storage.sql import get_alembic_config, handle_schema_errors
from dagster.seven import quote_plus as urlquote


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


def retry_pg_connection_fn(fn, retry_limit=20, retry_wait=0.2):
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
            sqlalchemy.exc.OperationalError,
        ) as exc:
            logging.warning("Retrying failed database connection")
            if retry_limit == 0:
                six.raise_from(DagsterPostgresException("too many retries for DB connection"), exc)

        time.sleep(retry_wait)
        retry_limit -= 1


def wait_for_connection(conn_string):
    retry_pg_connection_fn(lambda: psycopg2.connect(conn_string))
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
