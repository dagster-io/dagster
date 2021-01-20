# pylint: disable=print-call
import importlib
import pkgutil

import dagster
import sqlalchemy as sa


def check_schema_compat(schema):
    """We run this check to ensure that we don't have any schema columns that are incompatible with
    MySQL.
    """
    for name in dir(schema):
        obj = getattr(schema, name)
        if isinstance(obj, sa.Table):
            print(name, obj)
            for column in obj.columns:
                print(f"  -{column}: {column.type}")
                if isinstance(column.type, sa.types.VARCHAR):
                    raise Exception(
                        f"Column {column} is type VARCHAR; cannot use bare db.String type as "
                        "it is incompatible with certain databases (MySQL). Use either a "
                        "fixed-length db.String(123) or db.Text instead."
                    )
            print()


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
