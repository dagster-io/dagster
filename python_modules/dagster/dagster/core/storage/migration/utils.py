from contextlib import contextmanager

from alembic import op
from dagster import check
from sqlalchemy.engine import reflection


def get_inspector():
    # pylint: disable=no-member
    bind = op.get_context().bind
    return reflection.Inspector.from_engine(bind)


def get_table_names():
    return get_inspector().get_table_names()


def has_table(table_name):
    return table_name in get_table_names()


def has_column(table_name, column_name):
    if not has_table(table_name):
        return False
    columns = [x.get("name") for x in get_inspector().get_columns(table_name)]
    return column_name in columns


_UPGRADING_INSTANCE = None


@contextmanager
def upgrading_instance(instance):
    global _UPGRADING_INSTANCE  # pylint: disable=global-statement
    check.invariant(_UPGRADING_INSTANCE is None, "update already in progress")
    try:
        _UPGRADING_INSTANCE = instance
        yield
    finally:
        _UPGRADING_INSTANCE = None


def get_currently_upgrading_instance():
    global _UPGRADING_INSTANCE  # pylint: disable=global-statement
    check.invariant(_UPGRADING_INSTANCE is not None, "currently upgrading instance not set")
    return _UPGRADING_INSTANCE
