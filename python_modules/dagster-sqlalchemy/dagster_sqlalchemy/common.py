import sqlalchemy

from dagster import ExecutionContext, check

from dagster.core.execution_context import (
    SystemPipelineExecutionContext,
    SystemTransformExecutionContext,
)


class SqlAlchemyResource(object):
    def __init__(self, engine, mock_sql=False):
        self.engine = check.inst_param(engine, 'engine', sqlalchemy.engine.Engine)
        self.mock_sql = check.bool_param(mock_sql, 'mock_sql')


class DefaultSqlAlchemyResources(object):
    def __init__(self, sa):
        self.sa = check.inst_param(sa, 'sa', SqlAlchemyResource)


def check_supports_sql_alchemy_resource(pipeline_context):
    check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
    check.invariant(pipeline_context.resources is not None)
    check.invariant(
        hasattr(pipeline_context.resources, 'sa'),
        'Resources must have sa property be an object of SqlAlchemyResource',
    )
    check.inst(
        pipeline_context.resources.sa,
        SqlAlchemyResource,
        'Resources must have sa property be an object of SqlAlchemyResource',
    )
    return pipeline_context


def create_sqlalchemy_context_from_engine(engine, loggers=None):
    resources = DefaultSqlAlchemyResources(SqlAlchemyResource(engine))
    return ExecutionContext(loggers=loggers, resources=resources)


def _is_sqlite_context(transform_context):
    check.inst_param(transform_context, 'transform_context', SystemTransformExecutionContext)

    check_supports_sql_alchemy_resource(transform_context.legacy_context)
    return _is_sqlite_resource(transform_context.resources.sa)


def _is_sqlite_resource(sa_resource):
    check.inst_param(sa_resource, 'sa_resource', SqlAlchemyResource)
    raw_connection = sa_resource.engine.raw_connection()
    if not hasattr(raw_connection, 'connection'):
        return False

    # FIXME: This is an awful way to do this
    return type(raw_connection.connection).__module__ == 'sqlite3'


def execute_sql_text_on_context(transform_context, sql_text):
    check.inst_param(transform_context, 'transform_context', SystemTransformExecutionContext)
    check_supports_sql_alchemy_resource(transform_context)

    return execute_sql_text_on_sa_resource(transform_context.resources.sa, sql_text)


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
