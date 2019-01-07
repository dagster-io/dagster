import sqlalchemy

from dagster import (
    DependencyDefinition,
    SolidDefinition,
    OutputDefinition,
    InputDefinition,
    PipelineContextDefinition,
    PipelineDefinition,
    ResourceDefinition,
    Result,
    check,
    execute_pipeline,
    types,
)

from .math_test_db import in_mem_engine


def _is_sqlite_context(context):
    # check_supports_sql_alchemy_resource(context)
    raw_connection = context.resources.engine.raw_connection()
    if not hasattr(raw_connection, 'connection'):
        return False

    # FIXME: This is an awful way to do this
    return type(raw_connection.connection).__module__ == 'sqlite3'


def execute_sql_text_on_context(info, sql_text):
    # check_supports_sql_alchemy_resource(context)
    check.str_param(sql_text, 'sql_text')

    # if context.resources.sa.mock_sql:
    #     return

    engine = info.context.resources.engine

    if _is_sqlite_context(info.context):
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


def _create_sql_alchemy_transform_fn(sql_text):
    check.str_param(sql_text, 'sql_text')

    def transform_fn(info, _args):
        yield Result(execute_sql_text_on_context(info, sql_text))

    return transform_fn


def create_sql_statement_solid(name, sql_text, inputs=None):
    check.str_param(name, 'name')
    check.str_param(sql_text, 'sql_text')
    check.opt_list_param(inputs, 'inputs', of_type=InputDefinition)

    if inputs is None:
        inputs = []

    return SolidDefinition(
        name=name,
        transform_fn=_create_sql_alchemy_transform_fn(sql_text),
        inputs=inputs,
        outputs=[OutputDefinition()],
    )


InMemSqlLiteEngineResource = ResourceDefinition(
    resource_fn=lambda info: in_mem_engine(info.config['num_table']),
    config_field=types.Field(
        types.Dict(
            {'num_table': types.Field(types.String, is_optional=True, default_value='num_table')}
        )
    ),
)


def test_resource_format():
    sum_sql_text = '''CREATE TABLE sum_table AS
            SELECT num1, num2, num1 + num2 as sum FROM num_table'''

    sum_sq_sql_text = '''CREATE TABLE sum_sq_table AS
            SELECT num1, num2, sum, sum * sum as sum_sq FROM sum_table'''

    sum_sql_solid = create_sql_statement_solid('sum_sql_solid', sum_sql_text)

    sum_sq_sql_solid = create_sql_statement_solid(
        'sum_sq_sql_solid', sum_sq_sql_text, inputs=[InputDefinition(name=sum_sql_solid.name)]
    )

    pipeline = PipelineDefinition(
        name='kdjfkd',
        solids=[sum_sql_solid, sum_sq_sql_solid],
        context_definitions={
            'in_mem': PipelineContextDefinition(resources={'engine': InMemSqlLiteEngineResource})
        },
        dependencies={
            'sum_sq_sql_solid': {sum_sql_solid.name: DependencyDefinition(sum_sql_solid.name)}
        },
    )

    result = execute_pipeline(
        pipeline, {'context': {'in_mem': {'resources': {'engine': {'config': {}}}}}}
    )

    assert result.success


def test_resource_format_with_config():
    sum_sql_text = '''CREATE TABLE sum_table AS
            SELECT num1, num2, num1 + num2 as sum FROM passed_in'''

    sum_sq_sql_text = '''CREATE TABLE sum_sq_table AS
            SELECT num1, num2, sum, sum * sum as sum_sq FROM sum_table'''

    sum_sql_solid = create_sql_statement_solid('sum_sql_solid', sum_sql_text)

    sum_sq_sql_solid = create_sql_statement_solid(
        'sum_sq_sql_solid', sum_sq_sql_text, inputs=[InputDefinition(name=sum_sql_solid.name)]
    )

    pipeline = PipelineDefinition(
        name='kjdkfjd',
        solids=[sum_sql_solid, sum_sq_sql_solid],
        context_definitions={
            'in_mem': PipelineContextDefinition(resources={'engine': InMemSqlLiteEngineResource})
        },
        dependencies={
            'sum_sq_sql_solid': {sum_sql_solid.name: DependencyDefinition(sum_sql_solid.name)}
        },
    )

    result = execute_pipeline(
        pipeline,
        {'context': {'in_mem': {'resources': {'engine': {'config': {'num_table': 'passed_in'}}}}}},
    )

    assert result.success
