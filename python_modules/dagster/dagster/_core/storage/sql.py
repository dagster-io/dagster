import re
import threading
from functools import lru_cache
from string import Template
from typing import Any, Optional, Tuple, Union

import sqlalchemy as db
from alembic.command import downgrade, stamp, upgrade
from alembic.config import Config
from alembic.runtime.environment import EnvironmentContext
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from pandas import Timestamp
from sqlalchemy.engine import Connection
from sqlalchemy.ext.compiler import compiles
from sqlescapy import sqlescape
from typing_extensions import TypeAlias

from dagster._utils import file_relative_path

create_engine = db.create_engine  # exported


ALEMBIC_SCRIPTS_LOCATION = "dagster:_core/storage/alembic"

# Stand-in for a typed query object, which is only available in sqlalchemy 2+
SqlAlchemyQuery: TypeAlias = Any

# Stand-in for a typed row object, which is only available in sqlalchemy 2+
SqlAlchemyRow: TypeAlias = Any

AlembicVersion: TypeAlias = Tuple[Optional[str], Optional[Union[str, Tuple[str, ...]]]]


@lru_cache(maxsize=3)  # run, event, and schedule storages
def get_alembic_config(
    dunder_file: str,
    config_path: str = "alembic/alembic.ini",
    script_location: Optional[str] = None,
) -> Config:
    if not script_location:
        script_location = ALEMBIC_SCRIPTS_LOCATION

    alembic_config = Config(file_relative_path(dunder_file, config_path))
    alembic_config.set_main_option("script_location", script_location)
    return alembic_config


def run_alembic_upgrade(
    alembic_config: Config, conn: Connection, run_id: Optional[str] = None, rev: str = "head"
) -> None:
    alembic_config.attributes["connection"] = conn
    alembic_config.attributes["run_id"] = run_id
    upgrade(alembic_config, rev)


def run_alembic_downgrade(
    alembic_config: Config, conn: Connection, rev: str, run_id: Optional[str] = None
) -> None:
    alembic_config.attributes["connection"] = conn
    alembic_config.attributes["run_id"] = run_id
    downgrade(alembic_config, rev)


# Ensure that at most one thread can be stamping alembic revisions at once
_alembic_lock = threading.Lock()


def stamp_alembic_rev(alembic_config: Config, conn: Connection, rev: str = "head") -> None:
    with _alembic_lock:
        alembic_config.attributes["connection"] = conn
        stamp(alembic_config, rev)


def check_alembic_revision(alembic_config: Config, conn: Connection) -> AlembicVersion:
    with _alembic_lock:
        migration_context = MigrationContext.configure(conn)
        db_revision = migration_context.get_current_revision()
        script = ScriptDirectory.from_config(alembic_config)
        head_revision = script.as_revision_number("head")

    return (db_revision, head_revision)


def run_migrations_offline(
    context: EnvironmentContext, config: Config, target_metadata: db.MetaData
) -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    from sqlite3 import DatabaseError

    connectable = config.attributes.get("connection", None)

    if connectable is None:
        raise Exception(
            "No connection set in alembic config. If you are trying to run this script from the "
            "command line, STOP and read the README."
        )

    try:
        context.configure(
            url=connectable.url,
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )

        with context.begin_transaction():
            context.run_migrations()
    except DatabaseError as exc:
        # This is to deal with concurrent execution -- if this table already exists thanks to a
        # race with another process, we are fine and can continue.
        if "table alembic_version already exists" not in str(exc):
            raise


def run_migrations_online(
    context: EnvironmentContext, config: Config, target_metadata: db.MetaData
) -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    from sqlite3 import DatabaseError

    connection = config.attributes.get("connection", None)

    if connection is None:
        raise Exception(
            "No connection set in alembic config. If you are trying to run this script from the "
            "command line, STOP and read the README."
        )

    try:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

    except DatabaseError as exc:
        # This is to deal with concurrent execution -- if this table already exists thanks to a
        # race with another process, we are fine and can continue.
        if "table alembic_version already exists" not in str(exc):
            raise


# SQLAlchemy types, compiler directives, etc. to avoid pre-0.11.0 migrations
# as well as compiler directives to make cross-DB API semantics the same.

# 1: make MySQL dates equivalent to PG or Sqlite dates

MYSQL_DATE_PRECISION: int = 6
MYSQL_FLOAT_PRECISION: int = 32


# datetime issue fix from here: https://stackoverflow.com/questions/29711102/sqlalchemy-mysql-millisecond-or-microsecond-precision/29723278
@compiles(db.DateTime, "mysql")
def compile_datetime_and_add_precision_mysql(_element, _compiler, **_kw) -> str:
    return f"DATETIME({MYSQL_DATE_PRECISION})"


class get_current_timestamp(db.sql.expression.FunctionElement):
    """Like CURRENT_TIMESTAMP, but has the same semantics on MySQL, Postgres, and Sqlite."""

    type = db.types.DateTime()  # type: ignore


@compiles(get_current_timestamp, "mysql")
def compiles_get_current_timestamp_mysql(_element, _compiler, **_kw) -> str:
    return f"CURRENT_TIMESTAMP({MYSQL_DATE_PRECISION})"


@compiles(get_current_timestamp)
def compiles_get_current_timestamp_default(_element, _compiler, **_kw) -> str:
    return "CURRENT_TIMESTAMP"


@compiles(db.types.TIMESTAMP, "mysql")
def add_precision_to_mysql_timestamps(_element, _compiler, **_kw) -> str:
    return f"TIMESTAMP({MYSQL_DATE_PRECISION})"


@compiles(db.types.Float, "mysql")
def add_precision_to_mysql_floats(_element, _compiler, **_kw) -> str:
    """Forces floats to have minimum precision of 32, which converts the underlying type to be a
    double.  This is necessary because the default precision of floats is too low for some types,
    including unix timestamps, resulting in truncated values in MySQL.
    """
    return f"FLOAT({MYSQL_FLOAT_PRECISION})"


@compiles(db.types.FLOAT, "mysql")
def add_precision_to_mysql_FLOAT(_element, _compiler, **_kw) -> str:
    """Forces floats to have minimum precision of 32, which converts the underlying type to be a
    double.  This is necessary because the default precision of floats is too low for some types,
    including unix timestamps, resulting in truncated values in MySQL.
    """
    return f"FLOAT({MYSQL_FLOAT_PRECISION})"


class MySQLCompatabilityTypes:
    UniqueText = db.String(512)

class SqlQuery:
    """Class to parse SQL Query strings.
    """

    def __init__(self, query, **bindings):
        self.query: str = query
        self.bindings = bindings

    def parse_bindings(self) -> str:
        """Substitute parameters (e.g. $my_asset) with values.
        """
        replacements = {}
        for key, value in self.bindings.items():
            if isinstance(value, SqlQuery):
                replacements[key] = f"({value.parse_bindings()})"
            elif isinstance(value, str):
                try:
                    replacements[key] = f"{Timestamp(value)}"
                except ValueError:
                    replacements[key] = f"{sqlescape(value)}"
            elif isinstance(value, Timestamp):
                replacements[key] = f"{value}"
            elif isinstance(value, (int, float, bool)):
                replacements[key] = str(value)
            elif value is None:
                replacements[key] = "null"
            else:
                raise TypeError(
                    f"Replacement {key} of type {type(value)} is not accepted"
                )

        query_str = Template(self.query).safe_substitute(replacements)
        remaining_params = re.search(r"\$([a-zA-z_0-9]+)", query_str)
        if remaining_params is not None:
            raise ValueError(
                f"There are unparsed parameters remaining in the query: "
                f"{remaining_params.group()}"
            )

        return query_str

    @classmethod
    def from_file(cls, filename, **bindings):
        """Instantiate class using SQL file from an absolute path.
        """
        with open(filename, "r", encoding="utf-8") as f:
            query = f.read()

        return cls(query, **bindings)

    @classmethod
    def from_relative_path(cls, dunderfile, relative_path, **bindings):
        """Instantiate class using SQL file from a relative path.
        """
        filename = file_relative_path(dunderfile, relative_path)
        return cls.from_file(filename, **bindings)