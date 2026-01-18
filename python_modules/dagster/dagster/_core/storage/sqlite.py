import os
import sqlite3

import dagster._check as check

LAST_KNOWN_STAMPED_SQLITE_ALEMBIC_REVISION = "5771160a95ad"


def create_db_conn_string(base_dir: str, db_name: str) -> str:
    check.str_param(base_dir, "base_dir")
    check.str_param(db_name, "db_name")

    path_components = os.path.abspath(base_dir).split(os.sep)
    db_file = f"{db_name}.db"
    return "sqlite:///{}".format("/".join(path_components + [db_file]))


def create_in_memory_conn_string(db_name: str) -> str:
    # Uses a named file-based URL for the in-memory connection (as opposed to the :memory: url) so
    # that multiple instances can share the same logical DB across connections, while maintaining
    # separate DBs for different db names.  The latter is required to have both the run / event_log
    # in-memory implementations within the same process
    return f"sqlite:///file:{db_name}?mode=memory&uri=true&cache=shared"


def get_sqlite_version() -> str:
    return str(sqlite3.sqlite_version)
