# pylint chokes on the perfectly ok import from alembic.migration
import threading
from functools import lru_cache

import sqlalchemy as db
from alembic.command import downgrade, stamp, upgrade
from alembic.config import Config
from alembic.migration import MigrationContext  # pylint: disable=import-error
from alembic.script import ScriptDirectory
from sqlalchemy.ext.compiler import compiles

from dagster._utils import file_relative_path
from dagster._utils.log import quieten

create_engine = db.create_engine  # exported


ALEMBIC_SCRIPTS_LOCATION = "dagster:_core/storage/alembic"


@lru_cache(maxsize=3)  # run, event, and schedule storages
def get_alembic_config(dunder_file, config_path="alembic/alembic.ini", script_location=None):
    if not script_location:
        script_location = ALEMBIC_SCRIPTS_LOCATION

    alembic_config = Config(file_relative_path(dunder_file, config_path))
    alembic_config.set_main_option("script_location", script_location)
    return alembic_config


def run_alembic_upgrade(alembic_config, conn, run_id=None, rev="head"):
    alembic_config.attributes["connection"] = conn
    alembic_config.attributes["run_id"] = run_id
    upgrade(alembic_config, rev)


def run_alembic_downgrade(alembic_config, conn, rev, run_id=None):
    alembic_config.attributes["connection"] = conn
    alembic_config.attributes["run_id"] = run_id
    downgrade(alembic_config, rev)


# Ensure that at most one thread can be stamping alembic revisions at once
_alembic_lock = threading.Lock()


def stamp_alembic_rev(alembic_config, conn, rev="head", quiet=True):
    with _alembic_lock, quieten(quiet):
        alembic_config.attributes["connection"] = conn
        stamp(alembic_config, rev)


def check_alembic_revision(alembic_config, conn):
    with _alembic_lock:
        migration_context = MigrationContext.configure(conn)
        db_revision = migration_context.get_current_revision()
        script = ScriptDirectory.from_config(alembic_config)
        head_revision = script.as_revision_number("head")

    return (db_revision, head_revision)


def run_migrations_offline(context, config, target_metadata):
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
        if not "table alembic_version already exists" in str(exc):
            raise


def run_migrations_online(context, config, target_metadata):
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    from sqlite3 import DatabaseError

    connectable = config.attributes.get("connection", None)

    if connectable is None:
        raise Exception(
            "No connection set in alembic config. If you are trying to run this script from the "
            "command line, STOP and read the README."
        )

    with connectable.connect() as connection:
        try:
            context.configure(connection=connection, target_metadata=target_metadata)

            with context.begin_transaction():
                context.run_migrations()

        except DatabaseError as exc:
            # This is to deal with concurrent execution -- if this table already exists thanks to a
            # race with another process, we are fine and can continue.
            if not "table alembic_version already exists" in str(exc):
                raise


# SQLAlchemy types, compiler directives, etc. to avoid pre-0.11.0 migrations
# as well as compiler directives to make cross-DB API semantics the same.

# 1: make MySQL dates equivalent to PG or Sqlite dates

MYSQL_DATE_PRECISION: int = 6
MYSQL_FLOAT_PRECISION: int = 32

# datetime issue fix from here: https://stackoverflow.com/questions/29711102/sqlalchemy-mysql-millisecond-or-microsecond-precision/29723278
@compiles(db.DateTime, "mysql")
def compile_datetime_and_add_precision_mysql(_element, _compiler, **_kw):
    return f"DATETIME({MYSQL_DATE_PRECISION})"


class get_current_timestamp(db.sql.expression.FunctionElement):  # pylint: disable=abstract-method
    """Like CURRENT_TIMESTAMP, but has the same semantics on MySQL, Postgres, and Sqlite"""

    type = db.types.DateTime()


@compiles(get_current_timestamp, "mysql")
def compiles_get_current_timestamp_mysql(_element, _compiler, **_kw):
    return f"CURRENT_TIMESTAMP({MYSQL_DATE_PRECISION})"


@compiles(get_current_timestamp)
def compiles_get_current_timestamp_default(_element, _compiler, **_kw):
    return "CURRENT_TIMESTAMP"


@compiles(db.types.TIMESTAMP, "mysql")
def add_precision_to_mysql_timestamps(_element, _compiler, **_kw):
    return f"TIMESTAMP({MYSQL_DATE_PRECISION})"


@compiles(db.types.Float, "mysql")
def add_precision_to_mysql_floats(_element, _compiler, **_kw):
    """Forces floats to have minimum precision of 32, which converts the underlying type to be a
    double.  This is necessary because the default precision of floats is too low for some types,
    including unix timestamps, resulting in truncated values in MySQL"""
    return f"FLOAT({MYSQL_FLOAT_PRECISION})"


@compiles(db.types.FLOAT, "mysql")
def add_precision_to_mysql_FLOAT(_element, _compiler, **_kw):
    """Forces floats to have minimum precision of 32, which converts the underlying type to be a
    double.  This is necessary because the default precision of floats is too low for some types,
    including unix timestamps, resulting in truncated values in MySQL"""
    return f"FLOAT({MYSQL_FLOAT_PRECISION})"


class MySQLCompatabilityTypes:
    UniqueText = db.String(512)
