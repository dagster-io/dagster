# ruff: noqa: T201
import importlib
import pkgutil

import dagster
import sqlalchemy as db
from sqlalchemy.sql import elements as db_sql_elements
from sqlalchemy.sql.schema import Column


def check_schema_compat(schema):
    """We run this check to ensure that we don't have any schema columns that are incompatible with
    MySQL.
    """
    for name in dir(schema):
        obj = getattr(schema, name)
        if isinstance(obj, db.Table):
            print(name, obj)
            for column in obj.columns:
                print(f"  -{column}: {column.type};")
                if isinstance(column, Column):
                    validate_column(column)
            print()


def validate_column(column: Column):
    """This function is used to validate individual DB columns in a a schema for cross-DBAPI compatibility.

    i.e.:
        1. plain db.String not allowed (MySQL compatability)
        2. db.Text + unique=True not allowed (MySQL compatability).
    """
    if (
        isinstance(column.type, db.String)
        and not isinstance(column.type, (db.Text, db.Unicode))
        and column.type.length is None
    ):
        raise Exception(
            f"Column {column} is type VARCHAR; cannot use bare db.String type as "
            "it is incompatible with certain databases (MySQL). Use either a "
            "fixed-length db.String(123) or db.Text instead."
        )
    elif isinstance(column.type, db.Text) and column.unique:
        raise Exception(
            f"Column {column} is type TEXT and has a UNIQUE constraint; "
            "cannot use bare db.Text type w/ a UNIQUE constaint "
            "since it is incompatible with certain databases (MySQL). "
            "Use MySQLCompatabilityTypes.UniqueText or a fixed-length db.String(123) instead."
        )
    elif (
        column.server_default
        and isinstance(column.server_default.arg, db_sql_elements.TextClause)
        and str(column.server_default.arg) == "CURRENT_TIMESTAMP"
    ):
        raise Exception(
            f"Column {column} has a server default of CURRENT_TIMESTAMP without precision"
            " specified. To allow schema compatibility between MySQL, Postgres, and SQLite, use"
            " dagster._core.storage.sql.py::get_current_timestamp() instead."
        )


if __name__ == "__main__":
    schema_modules = set()

    def list_submodules(package):
        for _, module_name, is_pkg in pkgutil.walk_packages(
            package.__path__, package.__name__ + "."
        ):
            # Collect all of the dagster._core.storage.*.schema modules
            if module_name.endswith("schema"):
                schema_modules.add(module_name)

            module = __import__(module_name, fromlist="dummylist")
            if is_pkg:
                list_submodules(module)

    list_submodules(dagster._core.storage)  # pylint: disable=protected-access

    for schema_module in schema_modules:
        check_schema_compat(importlib.import_module(schema_module))
