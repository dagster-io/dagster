from alembic import op
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
    columns = [x.get('name') for x in get_inspector().get_columns(table_name)]
    return column_name in columns
