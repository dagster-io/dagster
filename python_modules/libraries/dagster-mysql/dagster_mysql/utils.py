import logging
import re
import time
from contextlib import contextmanager
from typing import Callable, Iterator, Optional, Tuple, TypeVar, Union, cast
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
from dagster._core.storage.config import MySqlStorageConfig
from dagster._core.storage.sql import get_alembic_config
from mysql.connector.pooling import PooledMySQLConnection
from sqlalchemy.engine import Connection
from typing_extensions import TypeAlias

T = TypeVar("T")

# Represents the output of mysql connection function
MySQLConnectionUnion: TypeAlias = Union[
    db.engine.Connection, mysql.MySQLConnection, PooledMySQLConnection
]


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


def mysql_url_from_config(config_value: MySqlStorageConfig) -> str:
    if config_value.get("mysql_url"):
        return config_value["mysql_url"]

    return get_conn_string(**config_value["mysql_db"])


def get_conn_string(
    username: str, password: str, hostname: str, db_name: str, port: Union[int, str] = "3306"
) -> str:
    return f"mysql+mysqlconnector://{username}:{urlquote(password)}@{hostname}:{port}/{db_name}"


def parse_mysql_version(version: str) -> Tuple[int, ...]:
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


def retry_mysql_creation_fn(
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
                and exc.errno == mysql_errorcode.ER_TABLE_EXISTS_ERROR
            ):
                raise
            logging.warning("Retrying failed database creation")
            if retry_limit == 0:
                raise DagsterMySQLException("too many retries for DB creation") from exc

        time.sleep(retry_wait)
        retry_limit -= 1


def retry_mysql_connection_fn(
    fn: Callable[[], T],
    retry_limit: int = 5,
    retry_wait: float = 0.2,
) -> T:
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


def mysql_isolation_level():
    if db.__version__.startswith("2.") or db.__version__.startswith("1.4"):
        # Starting with 1.4, the ability to emulate autocommit was deprecated, so we need to
        # explicitly call commit on the connection for MySQL where the AUTOCOMMIT isolation
        # level is not supported.  We should then set the isolation level to the MySQL default
        return "REPEATABLE READ"

    return "AUTOCOMMIT"


@contextmanager
def create_mysql_connection(
    engine: db.engine.Engine, dunder_file: str, storage_type_desc: Optional[str] = None
) -> Iterator[Connection]:
    check.inst_param(engine, "engine", db.engine.Engine)
    check.str_param(dunder_file, "dunder_file")
    check.opt_str_param(storage_type_desc, "storage_type_desc", "")

    if storage_type_desc:
        storage_type_desc += " "
    else:
        storage_type_desc = ""

    conn_cm = retry_mysql_connection_fn(engine.connect)
    with conn_cm as conn:
        with conn.begin():
            yield conn
