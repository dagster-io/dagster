import sqlalchemy as sa

from dagster import check
from dagster.core.execution import DagsterExecutionContext


class DagsterSqlAlchemyExecutionContext(DagsterExecutionContext):
    def __init__(self, engine, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.engine = check.inst_param(engine, 'engine', sa.engine.Engine)


def _is_sqlite_context(context):
    raw_connection = context.engine.raw_connection()
    if not hasattr(raw_connection, 'connection'):
        return False

    # FIXME: This is an awful way to do this
    return type(raw_connection.connection).__module__ == 'sqlite3'


def execute_sql_text_on_context(context, sql_text):
    check.inst_param(context, 'context', DagsterSqlAlchemyExecutionContext)
    check.str_param(sql_text, 'sql_text')

    if _is_sqlite_context(context):
        # sqlite3 does not support multiple statements in a single
        # sql text and sqlalchemy does not abstract that away AFAICT
        # so have to hack around this
        raw_connection = context.engine.raw_connection()
        cursor = raw_connection.cursor()
        try:
            cursor.executescript(sql_text)
            raw_connection.commit()
        finally:
            cursor.close()
    else:
        connection = context.engine.connect()
        transaction = connection.begin()
        connection.execute(sql_text)
        transaction.commit()
