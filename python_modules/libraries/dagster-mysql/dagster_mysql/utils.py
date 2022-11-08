import logging
import time
from contextlib import contextmanager
from urllib.parse import quote_plus as urlquote
from urllib.parse import urlparse

import mysql.connector as mysql
import sqlalchemy as db

from dagster import _check as check
from dagster._core.storage.sql import get_alembic_config


class DagsterMySQLException(Exception):
    pass


def get_conn(conn_string):
    parsed = urlparse(conn_string)
    conn = mysql.connect(
        user=parsed.username,
        passwd=parsed.password,
        host=parsed.hostname,
        database=parsed.path[1:],  # Skip first char, URL parser retains leading "/"
        port=parsed.port,
    )
    # https://github.com/dagster-io/dagster/issues/3735
    return conn


def mysql_url_from_config(config_value):
    if config_value.get("mysql_url"):
        return config_value["mysql_url"]

    return get_conn_string(**config_value["mysql_db"])


def get_conn_string(username, password, hostname, db_name, port="3306"):
    return "mysql+mysqlconnector://{username}:{password}@{hostname}:{port}/{db_name}".format(
        username=username,
        password=urlquote(password),
        hostname=hostname,
        db_name=db_name,
        port=port,
    )


def retry_mysql_creation_fn(fn, retry_limit=5, retry_wait=0.2):
    # Retry logic to recover from the case where two processes are creating
    # tables at the same time using sqlalchemy

    check.callable_param(fn, "fn")
    check.int_param(retry_limit, "retry_limit")
    check.numeric_param(retry_wait, "retry_wait")

    while True:
        try:
            return fn()
        except (
            mysql.ProgrammingError,
            mysql.IntegrityError,
            db.exc.ProgrammingError,
            db.exc.IntegrityError,
        ) as exc:
            if (
                isinstance(exc, db.exc.ProgrammingError)
                and exc.orig
                and exc.orig.errno == mysql.errorcode.ER_TABLE_EXISTS_ERROR
            ) or (
                isinstance(exc, mysql.ProgrammingError)
                and exc.errno == mysql.errorcode.ER_TABLE_EXISTS_ERROR
            ):
                raise
            logging.warning("Retrying failed database creation")
            if retry_limit == 0:
                raise DagsterMySQLException("too many retries for DB creation") from exc

        time.sleep(retry_wait)
        retry_limit -= 1


def retry_mysql_connection_fn(fn, retry_limit=5, retry_wait=0.2):
    """Reusable retry logic for any MySQL connection functions that may fail.
    Intended to be used anywhere we connect to MySQL, to gracefully handle transient connection
    issues.
    """
    check.callable_param(fn, "fn")
    check.int_param(retry_limit, "retry_limit")
    check.numeric_param(retry_wait, "retry_wait")

    while True:
        try:
            return fn()

        except (
            mysql.DatabaseError,
            mysql.OperationalError,
            db.exc.DatabaseError,
            db.exc.OperationalError,
            mysql.errors.InterfaceError,
        ) as exc:
            logging.warning("Retrying failed database connection")
            if retry_limit == 0:
                raise DagsterMySQLException("too many retries for DB connection") from exc

        time.sleep(retry_wait)
        retry_limit -= 1


def wait_for_connection(conn_string, retry_limit=5, retry_wait=0.2):
    parsed = urlparse(conn_string)
    retry_mysql_connection_fn(
        lambda: mysql.connect(
            user=parsed.username,
            passwd=parsed.password,
            host=parsed.hostname,
            database=parsed.path[1:],  # Skip first char, URL parser retains leading "/"
            port=parsed.port,
        ),
        retry_limit=retry_limit,
        retry_wait=retry_wait,
    )
    return True


def mysql_alembic_config(dunder_file):
    return get_alembic_config(dunder_file, config_path="../alembic/alembic.ini")


@contextmanager
def create_mysql_connection(engine, dunder_file, storage_type_desc=None):
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
        conn = retry_mysql_connection_fn(engine.connect)
        yield conn
    finally:
        if conn:
            conn.close()
