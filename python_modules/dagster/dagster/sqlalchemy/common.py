import sqlalchemy

from dagster import (
    ExecutionContext,
    check,
)


class SqlAlchemyResource(object):
    def __init__(self, engine, mock_sql=False):
        self.engine = check.inst_param(engine, 'engine', sqlalchemy.engine.Engine)
        self.mock_sql = check.bool_param(mock_sql, 'mock_sql')


class DefaultSqlAlchemyResources(object):
    def __init__(self, sa):
        self.sa = check.inst_param(sa, 'sa', SqlAlchemyResource)


def check_supports_sql_alchemy_resource(context):
    check.inst_param(context, 'context', ExecutionContext)
    check.invariant(context.resources is not None)
    check.invariant(
        hasattr(context.resources, 'sa'),
        'Resources must have sa property be an object of SqlAlchemyResource',
    )
    check.inst(
        context.resources.sa,
        SqlAlchemyResource,
        'Resources must have sa property be an object of SqlAlchemyResource',
    )
    return context


def create_sql_alchemy_context_from_sa_resource(sa_resource, *args, **kwargs):
    check.inst_param(sa_resource, 'sa_resource', SqlAlchemyResource)
    resources = DefaultSqlAlchemyResources(sa_resource)
    context = ExecutionContext(resources=resources, *args, **kwargs)
    return check_supports_sql_alchemy_resource(context)


def create_sql_alchemy_context_from_engine(engine, *args, **kwargs):
    resources = DefaultSqlAlchemyResources(SqlAlchemyResource(engine))
    context = ExecutionContext(resources=resources, *args, **kwargs)
    return check_supports_sql_alchemy_resource(context)


def _is_sqlite_context(context):
    check_supports_sql_alchemy_resource(context)
    raw_connection = context.resources.sa.engine.raw_connection()
    if not hasattr(raw_connection, 'connection'):
        return False

    # FIXME: This is an awful way to do this
    return type(raw_connection.connection).__module__ == 'sqlite3'


def execute_sql_text_on_context(context, sql_text):
    check_supports_sql_alchemy_resource(context)
    check.str_param(sql_text, 'sql_text')

    if context.resources.sa.mock_sql:
        return

    engine = context.resources.sa.engine

    if _is_sqlite_context(context):
        # sqlite3 does not support multiple statements in a single
        # sql text and sqlalchemy does not abstract that away AFAICT
        # so have to hack around this
        raw_connection = engine.raw_connection()
        cursor = raw_connection.cursor()
        try:
            cursor.executescript(sql_text)
            raw_connection.commit()
        finally:
            cursor.close()
    else:
        connection = engine.connect()
        transaction = connection.begin()
        connection.execute(sqlalchemy.text(sql_text))
        transaction.commit()
