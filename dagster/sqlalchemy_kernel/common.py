import sqlalchemy as sa

from dagster import check
from dagster.core.errors import DagsterInvariantViolationError


def _is_sqlite_context(context):
    raw_connection = context.environment['engine'].raw_connection()
    if not hasattr(raw_connection, 'connection'):
        return False

    # FIXME: This is an awful way to do this
    return type(raw_connection.connection).__module__ == 'sqlite3'


def execute_sql_text_on_context(context, sql_text):
    check.str_param(sql_text, 'sql_text')

    if 'engine' not in context.environment:
        raise DagsterInvariantViolationError(
            'Engine is not part of execution environment, make sure to pass `engine` to dagster execution environment.'
        )

    if _is_sqlite_context(context):
        # sqlite3 does not support multiple statements in a single
        # sql text and sqlalchemy does not abstract that away AFAICT
        # so have to hack around this
        raw_connection = context.environment['engine'].raw_connection()
        cursor = raw_connection.cursor()
        try:
            cursor.executescript(sql_text)
            raw_connection.commit()
        finally:
            cursor.close()
    else:
        connection = context.environment['engine'].connect()
        transaction = connection.begin()
        connection.execute(sql_text)
        transaction.commit()
