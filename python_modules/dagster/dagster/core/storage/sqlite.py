import sqlite3
from functools import update_wrapper

from .sql import run_migrations_offline as run_migrations_offline_
from .sql import run_migrations_online as run_migrations_online_


def run_migrations_offline(*args, **kwargs):
    try:
        run_migrations_offline_(*args, **kwargs)
    except sqlite3.DatabaseError as exc:
        # This is to deal with concurrent execution -- if this table already exists thanks to a
        # race with another process, we are fine and can continue.
        if not 'table alembic_version already exists' in str(exc):
            raise


def run_migrations_online(*args, **kwargs):
    try:
        run_migrations_online_(*args, **kwargs)
    except (sqlite3.DatabaseError, sqlite3.OperationalError) as exc:
        # This is to deal with concurrent execution -- if this table already exists thanks to a
        # race with another process, we are fine and can continue.
        if not 'table alembic_version already exists' in str(exc):
            raise


update_wrapper(run_migrations_offline, run_migrations_offline_)

update_wrapper(run_migrations_online, run_migrations_online_)
