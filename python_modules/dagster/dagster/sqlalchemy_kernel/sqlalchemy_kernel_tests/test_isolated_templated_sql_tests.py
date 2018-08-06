import dagster
from dagster import (config, check)
from dagster.core.definitions import (
    InputDefinition,
    SolidDefinition,
    SourceDefinition,
    ArgumentDefinition,
)
from dagster.sqlalchemy_kernel.templated import (
    _create_templated_sql_transform_with_output,
    _render_template_string,
    create_templated_sql_transform_solid,
)

from .math_test_db import in_mem_context


def _load_table(context, table_name):
    return context.resources.sa.engine.connect().execute(f'SELECT * FROM {table_name}').fetchall()


def table_name_source(table_name):
    check.str_param(table_name, 'table_name')
    return config.Source('TABLENAME', args={'name': table_name})


def pipeline_test_def(solids, context):
    return dagster.PipelineDefinition(
        solids=solids,
        context_definitions={
            'default':
            dagster.PipelineContextDefinition(
                argument_def_dict={},
                context_fn=lambda _pipeline, _args: context,
            ),
        }
    )


def test_single_templated_sql_solid_single_table_raw_api():
    sql = '''CREATE TABLE {{sum_table.name}}
    AS SELECT num1, num2, num1 + num2 as sum FROM num_table'''

    sum_table_arg = 'specific_sum_table'

    sum_table_input = InputDefinition(
        name='sum_table',
        sources=[
            SourceDefinition(
                source_type='TABLENAME',
                source_fn=lambda context, arg_dict: arg_dict,
                argument_def_dict={
                    'name': ArgumentDefinition(dagster.core.types.String),
                },
            )
        ]
    )

    sum_table_transform_solid = SolidDefinition(
        name='sum_table_transform',
        inputs=[sum_table_input],
        transform_fn=_create_templated_sql_transform_with_output(sql, 'sum_table'),
        output=dagster.OutputDefinition(),
    )

    pipeline = pipeline_test_def(solids=[sum_table_transform_solid], context=in_mem_context())
    environment = config.Environment(
        sources={'sum_table_transform': {
            'sum_table': table_name_source(sum_table_arg)
        }},
    )

    result = dagster.execute_pipeline(pipeline, environment=environment)
    assert result.success

    assert _load_table(result.context, sum_table_arg) == [(1, 2, 3), (3, 4, 7)]

    environment_without_source = config.Environment(
        sources={'sum_table_transform': {
            'sum_table': table_name_source('another_table')
        }},
    )
    result_no_source = dagster.execute_pipeline(pipeline, environment=environment_without_source)
    assert result_no_source.success

    assert _load_table(result_no_source.context, 'another_table') == [(1, 2, 3), (3, 4, 7)]


def test_single_templated_sql_solid_single_table_with_api():

    sql = '''CREATE TABLE {{sum_table.name}} AS
    SELECT num1, num2, num1 + num2 as sum FROM num_table'''

    sum_table_arg = 'specific_sum_table'

    sum_table_transform = create_templated_sql_transform_solid(
        name='sum_table_transform',
        sql=sql,
        table_arguments=['sum_table'],
        output='sum_table',
    )

    pipeline = pipeline_test_def(solids=[sum_table_transform], context=in_mem_context())

    environment = config.Environment(
        sources={'sum_table_transform': {
            'sum_table': table_name_source(sum_table_arg)
        }}
    )

    result = dagster.execute_pipeline(pipeline, environment=environment)
    assert result.success

    assert _load_table(result.context, sum_table_arg) == [(1, 2, 3), (3, 4, 7)]


def test_single_templated_sql_solid_double_table_raw_api():
    sum_table_arg = 'specific_sum_table'
    num_table_arg = 'specific_num_table'

    sql = '''CREATE TABLE {{sum_table.name}} AS
        SELECT num1, num2, num1 + num2 as sum FROM {{num_table.name}}'''

    sum_table_input = InputDefinition(
        name='sum_table',
        sources=[
            SourceDefinition(
                source_type='TABLENAME',
                source_fn=lambda context, arg_dict: arg_dict,
                argument_def_dict={
                    'name': ArgumentDefinition(dagster.core.types.String),
                },
            )
        ]
    )

    num_table_input = InputDefinition(
        name='num_table',
        sources=[
            SourceDefinition(
                source_type='TABLENAME',
                source_fn=lambda context, arg_dict: arg_dict,
                argument_def_dict={
                    'name': ArgumentDefinition(dagster.core.types.String),
                },
            )
        ]
    )

    sum_solid = SolidDefinition(
        name='sum_solid',
        inputs=[sum_table_input, num_table_input],
        transform_fn=_create_templated_sql_transform_with_output(
            sql,
            'sum_table',
        ),
        output=dagster.OutputDefinition(),
    )

    pipeline = pipeline_test_def(solids=[sum_solid], context=in_mem_context(num_table_arg))

    environment = config.Environment(
        sources={
            'sum_solid': {
                'sum_table': table_name_source(sum_table_arg),
                'num_table': table_name_source(num_table_arg),
            },
        },
    )

    result = dagster.execute_pipeline(pipeline, environment=environment)
    assert result.success

    assert _load_table(result.context, sum_table_arg) == [(1, 2, 3), (3, 4, 7)]


def test_single_templated_sql_solid_double_table_with_api():
    sum_table_arg = 'specific_sum_table'
    num_table_arg = 'specific_num_table'

    sql = '''CREATE TABLE {{sum_table.name}} AS
    SELECT num1, num2, num1 + num2 as sum FROM {{num_table.name}}'''

    sum_solid = create_templated_sql_transform_solid(
        name='sum_solid',
        sql=sql,
        table_arguments=['sum_table', 'num_table'],
        output='sum_table',
    )

    pipeline = pipeline_test_def(solids=[sum_solid], context=in_mem_context(num_table_arg))

    environment = config.Environment(
        sources={
            'sum_solid': {
                'sum_table': table_name_source(sum_table_arg),
                'num_table': table_name_source(num_table_arg),
            },
        },
    )

    result = dagster.execute_pipeline(pipeline, environment=environment)
    assert result.success

    assert _load_table(result.context, sum_table_arg) == [(1, 2, 3), (3, 4, 7)]


def test_templated_sql_solid_pipeline():
    sum_sql_template = '''CREATE TABLE {{sum_table.name}} AS
        SELECT num1, num2, num1 + num2 as sum FROM num_table'''

    sum_sq_sql_template = '''CREATE TABLE {{sum_sq_table.name}} AS
        SELECT num1, num2, sum, sum * sum as sum_sq FROM {{sum_table.name}}'''

    sum_solid = create_templated_sql_transform_solid(
        name='sum_table',
        sql=sum_sql_template,
        table_arguments=['sum_table'],
        output='sum_table',
    )

    sum_sq_solid = create_templated_sql_transform_solid(
        name='sum_sq_table',
        sql=sum_sq_sql_template,
        table_arguments=['sum_sq_table'],
        output='sum_sq_table',
        dependencies=[sum_solid],
    )

    context = in_mem_context()

    pipeline = pipeline_test_def(solids=[sum_solid, sum_sq_solid], context=context)
    first_sum_table = 'first_sum_table'
    first_sum_sq_table = 'first_sum_sq_table'

    environment_one = config.Environment(
        sources={
            'sum_table': {
                'sum_table': table_name_source(first_sum_table)
            },
            'sum_sq_table': {
                'sum_sq_table': table_name_source(first_sum_sq_table)
            },
        }
    )
    first_result = dagster.execute_pipeline(pipeline, environment=environment_one)
    assert first_result.success

    assert len(first_result.result_list) == 2
    assert first_result.result_list[0].transformed_value == {'name': first_sum_table}
    assert first_result.result_list[1].transformed_value == {'name': first_sum_sq_table}

    assert _load_table(first_result.context, first_sum_table) == [(1, 2, 3), (3, 4, 7)]

    assert _load_table(first_result.context, first_sum_sq_table) == [(1, 2, 3, 9), (3, 4, 7, 49)]

    # now execute subdag

    pipeline_two = pipeline_test_def(solids=[sum_solid, sum_sq_solid], context=context)

    second_sum_sq_table = 'second_sum_sq_table'

    environment_two = config.Environment(
        sources={
            'sum_sq_table': {
                'sum_table': table_name_source(first_sum_table),
                'sum_sq_table': table_name_source(second_sum_sq_table),
            },
        },
        execution=config.Execution.single_solid('sum_sq_table'),
    )

    second_result = dagster.execute_pipeline(
        pipeline_two,
        environment=environment_two,
    )
    assert second_result.success
    assert len(second_result.result_list) == 1
    assert _load_table(second_result.context, second_sum_sq_table) == [(1, 2, 3, 9), (3, 4, 7, 49)]


def test_templated_sql_solid_with_api():
    sql_template = '''CREATE TABLE {{sum_table.name}} AS
        SELECT num1, num2, num1 + num2 as sum FROM num_table'''

    sum_solid = create_templated_sql_transform_solid(
        name='sum_solid',
        sql=sql_template,
        table_arguments=['sum_table'],
        output='sum_table',
    )

    pipeline = pipeline_test_def(solids=[sum_solid], context=in_mem_context())

    sum_table_arg = 'specific_sum_table'
    environment = config.Environment(
        sources={'sum_solid': {
            'sum_table': table_name_source(sum_table_arg)
        }}
    )
    result = dagster.execute_pipeline(pipeline, environment=environment)
    assert result.success

    assert _load_table(result.context, sum_table_arg) == [(1, 2, 3), (3, 4, 7)]


def test_with_from_through_specifying_all_solids():
    pipeline = create_multi_input_pipeline()

    first_sum_table = 'first_sum_table'
    first_mult_table = 'first_mult_table'
    first_sum_mult_table = 'first_sum_mult_table'

    all_solid_names = [solid.name for solid in pipeline.solids]

    environment = config.Environment(
        sources={
            'sum_table': {
                'sum_table': table_name_source(first_sum_table),
            },
            'mult_table': {
                'mult_table': table_name_source(first_mult_table),
            },
            'sum_mult_table': {
                'sum_mult_table': table_name_source(first_sum_mult_table),
            },
        },
        execution=config.Execution(from_solids=all_solid_names, through_solids=all_solid_names)
    )

    pipeline_result = dagster.execute_pipeline(pipeline, environment=environment)
    assert len(pipeline_result.result_list) == 3
    assert _load_table(pipeline_result.context, first_sum_table) == [(1, 2, 3), (3, 4, 7)]
    assert _load_table(pipeline_result.context, first_mult_table) == [(1, 2, 2), (3, 4, 12)]
    assert _load_table(pipeline_result.context, first_sum_mult_table) == [(1, 3, 2), (3, 7, 12)]


def test_multi_input_partial_execution():
    pipeline = create_multi_input_pipeline()

    first_sum_table = 'first_sum_table'
    first_mult_table = 'first_mult_table'
    first_sum_mult_table = 'first_sum_mult_table'

    environment = config.Environment(
        sources={
            'sum_table': {
                'sum_table': table_name_source(first_sum_table),
            },
            'mult_table': {
                'mult_table': table_name_source(first_mult_table),
            },
            'sum_mult_table': {
                'sum_mult_table': table_name_source(first_sum_mult_table),
            },
        }
    )

    first_pipeline_result = dagster.execute_pipeline(pipeline, environment=environment)

    assert first_pipeline_result.success
    assert len(first_pipeline_result.result_list) == 3
    assert _load_table(first_pipeline_result.context, first_sum_table) == [(1, 2, 3), (3, 4, 7)]
    assert _load_table(first_pipeline_result.context, first_mult_table) == [(1, 2, 2), (3, 4, 12)]
    assert _load_table(first_pipeline_result.context,
                       first_sum_mult_table) == [(1, 3, 2), (3, 7, 12)]

    second_sum_mult_table = 'second_sum_mult_table'

    environment_two = config.Environment(
        sources={
            'sum_mult_table': {
                'sum_table': table_name_source(first_sum_table),
                'mult_table': table_name_source(first_mult_table),
                'sum_mult_table': table_name_source(second_sum_mult_table)
            },
        },
        execution=config.Execution.single_solid('sum_mult_table')
    )

    second_pipeline_result = dagster.execute_pipeline(
        pipeline,
        environment=environment_two,
    )

    assert second_pipeline_result.success
    assert len(second_pipeline_result.result_list) == 1
    assert _load_table(second_pipeline_result.context,
                       second_sum_mult_table) == [(1, 3, 2), (3, 7, 12)]


def create_multi_input_pipeline():
    sum_sql_template = '''CREATE TABLE {{sum_table.name}} AS
        SELECT num1, num2, num1 + num2 as sum FROM num_table'''

    mult_sql_template = '''CREATE TABLE {{mult_table.name}} AS
        SELECT num1, num2, num1 * num2 as mult FROM num_table'''

    sum_mult_join_template = '''CREATE TABLE {{sum_mult_table.name}} AS
        SELECT {{sum_table.name}}.num1, sum, mult FROM {{sum_table.name}}
        INNER JOIN {{mult_table.name}} ON {{sum_table.name}}.num1 = {{mult_table.name}}.num1'''

    sum_solid = create_templated_sql_transform_solid(
        name='sum_table',
        sql=sum_sql_template,
        table_arguments=['sum_table'],
        output='sum_table',
    )

    mult_solid = create_templated_sql_transform_solid(
        name='mult_table',
        sql=mult_sql_template,
        table_arguments=['mult_table'],
        output='mult_table',
    )

    sum_mult_solid = create_templated_sql_transform_solid(
        name='sum_mult_table',
        sql=sum_mult_join_template,
        table_arguments=['sum_mult_table'],
        dependencies=[sum_solid, mult_solid],
        output='sum_mult_table',
    )

    pipeline = pipeline_test_def(
        solids=[sum_solid, mult_solid, sum_mult_solid], context=in_mem_context()
    )
    return pipeline


def test_jinja():
    templated_sql = '''SELECT * FROM {{some_table.name}}'''

    sql = _render_template_string(templated_sql, args={'some_table': {'name': 'fill_me_in'}})

    assert sql == '''SELECT * FROM fill_me_in'''
