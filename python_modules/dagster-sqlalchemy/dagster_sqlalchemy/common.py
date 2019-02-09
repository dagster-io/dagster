import sqlalchemy

from dagster import ExecutionContext, check

from dagster.core.execution_context import TransformExecutionContext, LegacyRuntimeExecutionContext


class SqlAlchemyResource(object):
    def __init__(self, engine, mock_sql=False):
        self.engine = check.inst_param(engine, 'engine', sqlalchemy.engine.Engine)
        self.mock_sql = check.bool_param(mock_sql, 'mock_sql')


class DefaultSqlAlchemyResources(object):
    def __init__(self, sa):
        self.sa = check.inst_param(sa, 'sa', SqlAlchemyResource)


def check_supports_sql_alchemy_resource(legacy_context):
    check.inst_param(legacy_context, 'legacy_context', LegacyRuntimeExecutionContext)
    check.invariant(legacy_context.resources is not None)
    check.invariant(
        hasattr(legacy_context.resources, 'sa'),
        'Resources must have sa property be an object of SqlAlchemyResource',
    )
    check.inst(
        legacy_context.resources.sa,
        SqlAlchemyResource,
        'Resources must have sa property be an object of SqlAlchemyResource',
    )
    return legacy_context


def create_sql_alchemy_context_params_from_engine(engine, loggers=None):
    resources = DefaultSqlAlchemyResources(SqlAlchemyResource(engine))
    return ExecutionContext(loggers=loggers, resources=resources)


def _is_sqlite_context(context):
    check.inst_param(context, 'context', TransformExecutionContext)

    check_supports_sql_alchemy_resource(context.legacy_context)
    return _is_sqlite_resource(context.resources.sa)


def _is_sqlite_resource(sa_resource):
    check.inst_param(sa_resource, 'sa_resource', SqlAlchemyResource)
    raw_connection = sa_resource.engine.raw_connection()
    if not hasattr(raw_connection, 'connection'):
        return False

    # FIXME: This is an awful way to do this
    return type(raw_connection.connection).__module__ == 'sqlite3'


def execute_sql_text_on_context(context, sql_text):
    check.inst_param(context, 'context', TransformExecutionContext)
    check_supports_sql_alchemy_resource(context.legacy_context)

    return execute_sql_text_on_sa_resource(context.resources.sa, sql_text)


def execute_sql_text_on_sa_resource(sa_resource, sql_text):
    check.inst_param(sa_resource, 'sa_resource', SqlAlchemyResource)
    check.str_param(sql_text, 'sql_text')

    if sa_resource.mock_sql:
        return

    engine = sa_resource.engine

    if _is_sqlite_resource(sa_resource):
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
