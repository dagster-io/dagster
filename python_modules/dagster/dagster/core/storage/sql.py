# pylint chokes on the perfectly ok import from alembic.migration
import sys
import threading
from contextlib import contextmanager
from functools import lru_cache

import sqlalchemy as db
from alembic.command import downgrade, stamp, upgrade
from alembic.config import Config
from alembic.migration import MigrationContext  # pylint: disable=import-error
from alembic.script import ScriptDirectory
from dagster.core.errors import DagsterInstanceMigrationRequired
from dagster.utils import file_relative_path
from dagster.utils.log import quieten
from sqlalchemy.ext.compiler import compiles

create_engine = db.create_engine  # exported


@lru_cache(maxsize=3)  # run, event, and schedule storages
def get_alembic_config(dunder_file, config_path="alembic/alembic.ini", script_path="alembic/"):
    alembic_config = Config(file_relative_path(dunder_file, config_path))
    alembic_config.set_main_option("script_location", file_relative_path(dunder_file, script_path))
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
    migration_context = MigrationContext.configure(conn)
    db_revision = migration_context.get_current_revision()
    script = ScriptDirectory.from_config(alembic_config)
    head_revision = script.as_revision_number("head")

    return (db_revision, head_revision)


@contextmanager
def handle_schema_errors(conn, alembic_config, msg=None):
    try:
        yield
    except (db.exc.OperationalError, db.exc.ProgrammingError, db.exc.StatementError):
        db_revision, head_revision = (None, None)

        try:
            with quieten():
                db_revision, head_revision = check_alembic_revision(alembic_config, conn)
        # If exceptions were raised during the revision check, we want to swallow them and
        # allow the original exception to fall through
        except Exception:  # pylint: disable=broad-except
            pass

        if db_revision != head_revision:
            # Disable exception chaining since the original exception is included in the
            # message, and the fact that the instance needs migrating should be the first
            # thing the user sees
            raise DagsterInstanceMigrationRequired(
                msg=msg,
                db_revision=db_revision,
                head_revision=head_revision,
                original_exc_info=sys.exc_info(),
            ) from None

        raise


def run_migrations_offline(context, config, target_metadata):
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    connectable = config.attributes.get("connection", None)

    if connectable is None:
        raise Exception(
            "No connection set in alembic config. If you are trying to run this script from the "
            "command line, STOP and read the README."
        )

    context.configure(
        url=connectable.url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online(context, config, target_metadata):
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connection = config.attributes.get("connection", None)

    if connection is None:
        raise Exception(
            "No connection set in alembic config. If you are trying to run this script from the "
            "command line, STOP and read the README."
        )

    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


# SQLAlchemy types, compiler directives, etc. to avoid pre-0.11.0 migrations
# as well as compiler directives to make cross-DB API semantics the same.

# 1: make MySQL dates equivalent to PG or Sqlite dates

MYSQL_DATE_PRECISION: int = 6

# datetime issue fix from here: https://stackoverflow.com/questions/29711102/sqlalchemy-mysql-millisecond-or-microsecond-precision/29723278
@compiles(db.DateTime, "mysql")
def compile_datetime_and_add_precision_mysql(_element, _compiler, **_kw):
    return f"DATETIME({MYSQL_DATE_PRECISION})"


class get_current_timestamp(db.sql.expression.FunctionElement):
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


class MySQLCompatabilityTypes:
    UniqueText = db.String(512)
