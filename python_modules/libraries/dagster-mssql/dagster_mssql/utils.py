import logging
import time
import urllib
from contextlib import contextmanager

import pyodbc
import sqlalchemy as db

from dagster import Field, IntSource, StringSource, check
from dagster.core.storage.sql import get_alembic_config, handle_schema_errors
from sqlalchemy.ext.compiler import compiles


MSSQL_POOL_RECYCLE = 3600


class DagsterMSSQLException(Exception):
    pass


def mssql_config():
    return {
        "mssql_url": Field(StringSource, is_required=False),
        "mssql_db": Field(
            {
                "username": StringSource,
                "password": StringSource,
                "hostname": StringSource,
                "db_name": StringSource,
                "port": Field(IntSource, is_required=False, default_value=1433),
                "driver": Field(StringSource, is_required=False, default_value="{ODBC Driver 17 for SQL Server}"),
                "driver_opts": Field(StringSource, is_required=False, default_value="")
            },
            is_required=False,
        ),
        "should_autocreate_tables": Field(bool, is_required=False, default_value=True),
    }


def mssql_url_from_config(config_value):
    if config_value.get("mssql_url"):
        check.invariant(
            not "mssql_db" in config_value,
            "mssql storage config must have exactly one of `mssql_url` or `mssql_db`",
        )
        return config_value["mssql_url"]
    else:
        check.invariant(
            "mssql_db" in config_value,
            "mssql storage config must have exactly one of `mssql_url` or `mssql_db`",
        )

        return get_conn_string(**config_value["mssql_db"])


def get_conn_string(username, password, hostname, db_name, port="1433", driver="{ODBC Driver 17 for SQL Server}",
                    driver_opts=""):
    params = urllib.parse.quote_plus(f"DRIVER={driver};"
                                     f"SERVER={hostname};"
                                     f"DATABASE={db_name};"
                                     f"UID={username};"
                                     f"PWD={password};"
                                     f"PORT={port};"
                                     f"{driver_opts}")
    return f"mssql+pyodbc:///?odbc_connect={params}"


def retry_mssql_creation_fn(fn, retry_limit=5, retry_wait=0.2):
    # Retry logic to recover from the case where two processes are creating
    # tables at the same time using sqlalchemy

    check.callable_param(fn, "fn")
    check.int_param(retry_limit, "retry_limit")
    check.numeric_param(retry_wait, "retry_wait")

    while True:
        try:
            return fn()
        except (
            pyodbc.ProgrammingError,
            pyodbc.IntegrityError,
            db.exc.ProgrammingError,
            db.exc.IntegrityError,
        ) as exc:
            logging.warning("Retrying failed database creation")
            if retry_limit == 0:
                raise DagsterMSSQLException("too many retries for DB creation") from exc

        time.sleep(retry_wait)
        retry_limit -= 1


def retry_mssql_connection_fn(fn, retry_limit=5, retry_wait=0.2):
    """Reusable retry logic for any MSSQL connection functions that may fail.
    Intended to be used anywhere we connect to MSSQL, to gracefully handle transient connection
    issues.
    """
    check.callable_param(fn, "fn")
    check.int_param(retry_limit, "retry_limit")
    check.numeric_param(retry_wait, "retry_wait")

    while True:
        try:
            return fn()

        except (
            pyodbc.DatabaseError,
            pyodbc.OperationalError,
            db.exc.DatabaseError,
            db.exc.OperationalError,
        ) as exc:
            logging.warning("Retrying failed database connection")
            if retry_limit == 0:
                raise DagsterMSSQLException("too many retries for DB connection") from exc

        time.sleep(retry_wait)
        retry_limit -= 1


def wait_for_connection(conn_string, retry_limit=5, retry_wait=0.2):
    retry_mssql_connection_fn(
        lambda: pyodbc.connect(conn_string), retry_limit=retry_limit, retry_wait=retry_wait,
    )
    return True


def mssql_alembic_config(dunder_file):
    return get_alembic_config(
        dunder_file, config_path="../alembic/alembic.ini", script_path="../alembic/"
    )


@contextmanager
def create_mssql_connection(engine, dunder_file, storage_type_desc=None):
    check.inst_param(engine, "engine", db.engine.Engine)
    check.str_param(dunder_file, "dunder_file")
    check.opt_str_param(storage_type_desc, "storage_type_desc", "")

    if storage_type_desc:
        storage_type_desc += " "
    else:
        storage_type_desc = ""

    conn = None
    try:
        # Retry connection to gracefully handle transient connection issues
        conn = retry_mssql_connection_fn(engine.connect)
        with handle_schema_errors(
            conn,
            mssql_alembic_config(dunder_file),
            msg="MSSQL {}storage requires migration".format(storage_type_desc),
        ):
            yield conn
    finally:
        if conn:
            conn.close()


@compiles(db.types.TIMESTAMP, "mssql")
def compile_timestamp_mssql(_element, _compiler, **_kw):
    return f"DATETIME2"


@compiles(db.DateTime, "mssql")
def compile_datetime_mssql(_element, _compiler, **_kw):
    return f"DATETIME2"
