import os
import sqlite3

import dagster._check as check


def create_db_conn_string(base_dir, db_name):
    check.str_param(base_dir, "base_dir")
    check.str_param(db_name, "db_name")

    path_components = os.path.abspath(base_dir).split(os.sep)
    db_file = "{}.db".format(db_name)
    return "sqlite:///{}".format("/".join(path_components + [db_file]))


def get_sqlite_version():
    return str(sqlite3.sqlite_version)
