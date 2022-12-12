import logging
import re
import time
from contextlib import contextmanager
from typing import Callable, Optional, Union, cast
from urllib.parse import (
    quote_plus as urlquote,
    urlparse,
)

import mysql.connector as mysql
import mysql.connector.errorcode as mysql_errorcode
import sqlalchemy as db
import sqlalchemy.exc as db_exc
from alembic.config import Config
from dagster import _check as check
from dagster._core.storage.sql import get_alembic_config
from mysql.connector.pooling import PooledMySQLConnection
from typing_extensions import TypeAlias

# Represents the output of mysql connection function
MySQLConnectionUnion: TypeAlias = Union[mysql.MySQLConnection, PooledMySQLConnection]


class DagsterMySQLException(Exception):
    pass


def get_conn(conn_string: str) -> MySQLConnectionUnion:
    parsed = urlparse(conn_string)
    conn = cast(
        MySQLConnectionUnion,
        mysql.connect(
            user=parsed.username,
            passwd=parsed.password,
            host=parsed.hostname,
            database=parsed.path[1:],  # Skip first char, URL parser retains leading "/"
            port=parsed.port,
        ),
    )
    # https://github.com/dagster-io/dagster/issues/3735
    return conn


def mysql_url_from_config(config_value):
    if config_value.get("mysql_url"):
        return config_value["mysql_url"]

    return get_conn_string(**config_value["mysql_db"])


def get_conn_string(
    username: str, password: str, hostname: str, db_name: str, port: str = "3306"
) -> str:
    return "mysql+mysqlconnector://{username}:{password}@{hostname}:{port}/{db_name}".format(
        username=username,
        password=urlquote(password),
        hostname=hostname,
        db_name=db_name,
        port=port,
    )


def parse_mysql_version(version: str) -> tuple:
    """Parse MySQL version into a tuple of ints.

    Args:
        version (str): MySQL version string.

    Returns:
        tuple: Tuple of ints representing the MySQL version.
    """
    parsed = []
    for part in re.split(r"\D+", version):
        if len(part) == 0:
            continue
        try:
            parsed.append(int(part))
        except ValueError:
            continue
    return tuple(parsed)


def retry_mysql_creation_fn(fn, retry_limit: int = 5, retry_wait: float = 0.2):
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
            db_exc.ProgrammingError,
            db_exc.IntegrityError,
        ) as exc:
            if (
                isinstance(exc, db_exc.ProgrammingError)
                and exc.orig
                and exc.orig.errno == mysql_errorcode.ER_TABLE_EXISTS_ERROR
            ) or (
                isinstance(exc, mysql.ProgrammingError)
                and exc.errno == mysql_errorcode.ER_TABLE_EXISTS_ERROR  # type: ignore
            ):
                raise
            logging.warning("Retrying failed database creation")
            if retry_limit == 0:
                raise DagsterMySQLException("too many retries for DB creation") from exc

        time.sleep(retry_wait)
        retry_limit -= 1


def retry_mysql_connection_fn(
    fn: Callable[[], MySQLConnectionUnion],
    retry_limit: int = 5,
    retry_wait: float = 0.2,
) -> MySQLConnectionUnion:
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
            db_exc.DatabaseError,
            db_exc.OperationalError,
            mysql.errors.InterfaceError,
        ) as exc:
            logging.warning("Retrying failed database connection")
            if retry_limit == 0:
                raise DagsterMySQLException("too many retries for DB connection") from exc

        time.sleep(retry_wait)
        retry_limit -= 1


def wait_for_connection(conn_string: str, retry_limit: int = 5, retry_wait: float = 0.2) -> bool:
    parsed = urlparse(conn_string)
    retry_mysql_connection_fn(
        lambda: cast(
            Union[mysql.MySQLConnection, PooledMySQLConnection],
            mysql.connect(
                user=parsed.username,
                passwd=parsed.password,
                host=parsed.hostname,
                database=parsed.path[1:],  # Skip first char, URL parser retains leading "/"
                port=parsed.port,
            ),
        ),
        retry_limit=retry_limit,
        retry_wait=retry_wait,
    )
    return True


def mysql_alembic_config(dunder_file: str) -> Config:
    return get_alembic_config(dunder_file, config_path="../alembic/alembic.ini")


@contextmanager
def create_mysql_connection(
    engine: db.engine.Engine, dunder_file: str, storage_type_desc: Optional[str] = None
):
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
