import threading
from functools import lru_cache
from typing import Any, TypeAlias

import sqlalchemy as db
from alembic.command import downgrade, stamp, upgrade
from alembic.config import Config
from alembic.runtime.environment import EnvironmentContext
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.engine import Connection
from sqlalchemy.ext.compiler import compiles

from dagster._utils import file_relative_path

create_engine = db.create_engine  # exported


ALEMBIC_SCRIPTS_LOCATION = "dagster:_core/storage/alembic"

# Stand-in for a typed query object, which is only available in sqlalchemy 2+
SqlAlchemyQuery: TypeAlias = Any

# Stand-in for a typed row object, which is only available in sqlalchemy 2+
SqlAlchemyRow: TypeAlias = Any

AlembicVersion: TypeAlias = tuple[str | None, str | tuple[str, ...] | None]


@lru_cache(maxsize=3)  # run, event, and schedule storages
def get_alembic_config(
    dunder_file: str,
    config_path: str = "alembic/alembic.ini",
    script_location: str | None = None,
) -> Config:
    if not script_location:
        script_location = ALEMBIC_SCRIPTS_LOCATION

    alembic_config = Config(file_relative_path(dunder_file, config_path))
    alembic_config.set_main_option("script_location", script_location)
    return alembic_config


def run_alembic_upgrade(
    alembic_config: Config, conn: Connection, run_id: str | None = None, rev: str = "head"
) -> None:
    alembic_config.attributes["connection"] = conn
    alembic_config.attributes["run_id"] = run_id
    upgrade(alembic_config, rev)


def run_alembic_downgrade(
    alembic_config: Config, conn: Connection, rev: str, run_id: str | None = None
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


def safe_commit(conn: Connection) -> None:
    """Commits to a connection if it is in a transaction. Supports compatibility across SQLAlchemy versions,
    since older versions (1.3) have autocommit on transactions, instead of explicit commits.
    """
    if not conn.in_transaction():
        return
    if hasattr(conn, "commit"):
        conn.commit()  # type: ignore


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


class get_sql_current_timestamp(db.sql.expression.FunctionElement):
    """Like CURRENT_TIMESTAMP, but has the same semantics on MySQL, Postgres, and Sqlite."""

    type = db.types.DateTime()


@compiles(get_sql_current_timestamp, "mysql")
def compiles_get_sql_current_timestamp_mysql(_element, _compiler, **_kw) -> str:
    return f"CURRENT_TIMESTAMP({MYSQL_DATE_PRECISION})"


@compiles(get_sql_current_timestamp)
def compiles_get_sql_current_timestamp_default(_element, _compiler, **_kw) -> str:
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


class LongText(db.Text):
    """Allows customization of certain fields to map to LONGTEXT in MySQL.  For Postgres, all text
    fields are mapped to TEXT, which is unbounded in length, so the distinction is not neccessary.
    In MySQL, however, TEXT is limited to 64KB, so LONGTEXT (4GB) is required for certain fields.
    """

    pass


@compiles(LongText, "mysql")
def compile_longtext_mysql(_element, _compiler, **_kw) -> str:
    return "LONGTEXT"


# 2: make SQL Server dates, text and identifiers equivalent to PG or MySQL

MSSQL_DATE_PRECISION: int = 6

# SQL Server's nonclustered index key is limited to 1700 bytes, and NVARCHAR costs two
# bytes per character, so every text column that participates in an index key has to be
# given an explicit bound.  See `mssql_text` below.
MSSQL_INDEX_KEY_LENGTH: int = 256


@compiles(db.types.TIMESTAMP, "mssql")
def compile_timestamp_mssql(_element, _compiler, **_kw) -> str:
    """A bare TIMESTAMP column on SQL Server is a synonym for ROWVERSION -- an
    auto-generated binary counter, not a point in time -- and a table may only have one of
    them.  DATETIME2 is the actual timestamp type.
    """
    return f"DATETIME2({MSSQL_DATE_PRECISION})"


@compiles(db.DateTime, "mssql")
def compile_datetime_and_add_precision_mssql(_element, _compiler, **_kw) -> str:
    """DATETIME on SQL Server only resolves to ~3.33ms, which is too coarse for the
    timestamp comparisons dagster does when paginating ticks and runs.
    """
    return f"DATETIME2({MSSQL_DATE_PRECISION})"


@compiles(get_sql_current_timestamp, "mssql")
def compiles_get_sql_current_timestamp_mssql(_element, _compiler, **_kw) -> str:
    # CURRENT_TIMESTAMP on SQL Server is server-local and only DATETIME precision
    return "SYSUTCDATETIME()"


def mssql_text(index_key_length: int | None = None) -> db.Text:
    """A Text column that is also valid, and lossless, on SQL Server.

    Two things differ from Postgres and MySQL:

    * ``db.Text`` renders as ``VARCHAR(max)``, which SQL Server refuses to use as an index
      key column.  Columns that appear in an index must be given a bounded length --
      ``index_key_length`` -- which is the SQL Server analogue of the prefix lengths
      dagster-mysql indexes these same columns with via ``mysql_length``.  Unlike a MySQL
      prefix index the bound applies to storage as well, but SQL Server raises rather than
      truncating, so an over-long value fails loudly instead of corrupting.
    * ``VARCHAR`` stores text in the database's codepage, so under any non-UTF-8 collation
      every character outside it is silently replaced with ``?``.  Asset keys, partition
      keys and run tags are written as raw strings, so that is real data loss.  Binding
      them as ``NVARCHAR`` makes storage independent of the server's collation, which
      matters because UTF-8 collations only exist on SQL Server 2019 and later.

    ``db.UnicodeText`` deliberately is not used here: it renders as ``NTEXT``, which is
    deprecated and, like ``VARCHAR(max)``, cannot be indexed.

    ``with_variant`` leaves the DDL *and* the bind-parameter handling of every other
    dialect completely untouched.
    """
    return db.Text().with_variant(db.NVARCHAR(index_key_length), "mssql")


def mssql_string(length: int) -> db.String:
    """A String column that stores Unicode independently of the server collation.

    Same codepage reasoning as :py:func:`mssql_text`; ``db.String`` renders as ``VARCHAR``
    on SQL Server, so a bounded string holding user data needs the same treatment.
    """
    return db.String(length).with_variant(db.NVARCHAR(length), "mssql")


class MySQLCompatabilityTypes:
    # Bounded rather than TEXT because MySQL cannot put a unique constraint on a TEXT
    # column, and NVARCHAR on SQL Server for the collation reasons described above.
    UniqueText = mssql_string(512)
    # An instance rather than the class, so that the SQL Server variant carries through to
    # bind-parameter handling and not just the emitted DDL.  A compiler directive alone
    # would declare the column NVARCHAR while still binding values as VARCHAR, which is
    # exactly the silent-corruption case `mssql_text` describes.
    LongText = LongText().with_variant(db.NVARCHAR(None), "mssql")
