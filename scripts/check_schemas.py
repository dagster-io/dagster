# pylint: disable=print-call
import importlib
import pkgutil

import dagster
import sqlalchemy as db
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


# These columns (in dagster/core/storage/*/schema.py) need
# migration or a compiles directive to be compatible with MySQL.
MYSQL_MIGRATION_PLANNED_COLUMNS = frozenset(["secondary_indexes.name", "asset_keys.asset_key"])


def validate_column(column: Column):
    """This function is used to validate individual DB columns in a a schema for cross-DBAPI compatibility
    i.e.:
        1. plain db.String not allowed (MySQL compatability)
        2. db.Text + unique=True not allowed (MySQL compatability)
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
    elif (
        isinstance(column.type, db.Text)
        and column.unique
        and str(column) not in MYSQL_MIGRATION_PLANNED_COLUMNS
    ):
        raise Exception(
            f"Column {column} is type TEXT and has a UNIQUE constraint; "
            "cannot use bare db.Text type w/ a UNIQUE constaint "
            "since it is incompatible with certain databases (MySQL). "
            "Use a fixed-length db.String(123) instead."
        )


if __name__ == "__main__":
    schema_modules = set()

    def list_submodules(package_name):
        for _, module_name, is_pkg in pkgutil.walk_packages(
            package_name.__path__, package_name.__name__ + "."
        ):
            # Collect all of the dagster.core.storage.*.schema modules
            if module_name.endswith("schema"):
                schema_modules.add(module_name)

            module_name = __import__(module_name, fromlist="dummylist")
            if is_pkg:
                list_submodules(module_name)

    list_submodules(dagster.core.storage)

    for schema_module in schema_modules:
        check_schema_compat(importlib.import_module(schema_module))
