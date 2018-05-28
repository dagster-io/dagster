import dagster
from dagster import check
from dagster.core.definitions import (Solid, InputDefinition)
from .math_test_db import in_mem_context

from dagster.sqlalchemy_kernel.templated import (
    _create_templated_sql_transform_with_output, create_templated_sql_transform_solid,
    _render_template_string
)


def _load_table(context, table_name):
    return context.engine.connect().execute(f'SELECT * FROM {table_name}').fetchall()


def test_single_templated_sql_solid_single_table_raw_api():
    context = in_mem_context()

    sql = '''CREATE TABLE {{sum_table.name}} 
    AS SELECT num1, num2, num1 + num2 as sum FROM num_table'''

    sum_table_arg = 'specific_sum_table'

    sum_table_input = InputDefinition(
        name='sum_table',
        input_fn=lambda arg_dict: arg_dict,
        argument_def_dict={'name': dagster.core.types.STRING}
    )

    sum_table_transform_solid = Solid(
        name='sum_table_transform',
        inputs=[sum_table_input],
        transform_fn=_create_templated_sql_transform_with_output(sql, 'sum_table'),
        outputs=[],
    )

    pipeline = dagster.pipeline(solids=[sum_table_transform_solid])

    input_arg_dict = {'sum_table': {'name': sum_table_arg}}
    result = dagster.execute_pipeline(context, pipeline, input_arg_dict)
    assert result.success

    assert _load_table(context, sum_table_arg) == [(1, 2, 3), (3, 4, 7)]


def test_single_templated_sql_solid_single_table_with_api():
    context = in_mem_context()

    sql = '''CREATE TABLE {{sum_table.name}} AS
    SELECT num1, num2, num1 + num2 as sum FROM num_table'''

    sum_table_arg = 'specific_sum_table'

    sum_table_transform = create_templated_sql_transform_solid(
        name='sum_table_transform',
        sql=sql,
        table_arguments=['sum_table'],
        dependencies=[],
        output='sum_table',
    )

    pipeline = dagster.pipeline(solids=[sum_table_transform])

    input_arg_dict = {'sum_table': {'name': sum_table_arg}}
    result = dagster.execute_pipeline(context, pipeline, input_arg_dict)
    assert result.success

    assert _load_table(context, sum_table_arg) == [(1, 2, 3), (3, 4, 7)]


def test_single_templated_sql_solid_double_table_raw_api():
    sum_table_arg = 'specific_sum_table'
    num_table_arg = 'specific_num_table'

    context = in_mem_context(num_table_arg)

    sql = '''CREATE TABLE {{sum_table.name}} AS
        SELECT num1, num2, num1 + num2 as sum FROM {{num_table.name}}'''

    sum_table_input = InputDefinition(
        name='sum_table',
        input_fn=lambda arg_dict: arg_dict,
        argument_def_dict={
            'name': dagster.core.types.STRING,
        }
    )

    num_table_input = InputDefinition(
        name='num_table',
        input_fn=lambda arg_dict: arg_dict,
        argument_def_dict={
            'name': dagster.core.types.STRING,
        }
    )

    sum_solid = Solid(
        name='sum_solid',
        inputs=[sum_table_input, num_table_input],
        transform_fn=_create_templated_sql_transform_with_output(
            sql,
            'sum_table',
        ),
        outputs=[],
    )

    pipeline = dagster.pipeline(solids=[sum_solid])

    input_arg_dict = {
        'sum_table': {
            'name': sum_table_arg
        },
        'num_table': {
            'name': num_table_arg
        },
    }

    result = dagster.execute_pipeline(context, pipeline, input_arg_dict)
    assert result.success

    assert _load_table(context, sum_table_arg) == [(1, 2, 3), (3, 4, 7)]


def test_single_templated_sql_solid_double_table_with_api():
    sum_table_arg = 'specific_sum_table'
    num_table_arg = 'specific_num_table'

    context = in_mem_context(num_table_arg)

    sql = '''CREATE TABLE {{sum_table.name}} AS SELECT num1, num2, num1 + num2 as sum FROM {{num_table.name}}'''

    sum_solid = create_templated_sql_transform_solid(
        name='sum_solid',
        sql=sql,
        table_arguments=['sum_table', 'num_table'],
        dependencies=[],
        output='sum_table',
    )

    pipeline = dagster.pipeline(solids=[sum_solid])

    input_arg_dict = {
        'sum_table': {
            'name': sum_table_arg
        },
        'num_table': {
            'name': num_table_arg
        },
    }

    result = dagster.execute_pipeline(context, pipeline, input_arg_dict)
    assert result.success

    assert _load_table(context, sum_table_arg) == [(1, 2, 3), (3, 4, 7)]


def _args_input(input_name, args, depends_on=None):
    check.str_param(input_name, 'input_name')
    check.list_param(args, 'args', of_type=str)

    def input_fn(arg_dict):
        return arg_dict

    return InputDefinition(
        name=input_name,
        input_fn=input_fn,
        argument_def_dict={arg: dagster.core.types.STRING
                           for arg in args},
        depends_on=depends_on,
    )


def test_templated_sql_solid_pipeline():
    context = in_mem_context()

    sum_sql_template = '''CREATE TABLE {{sum_table.name}} AS
        SELECT num1, num2, num1 + num2 as sum FROM num_table'''

    sum_sq_sql_template = '''CREATE TABLE {{sum_sq_table.name}} AS
        SELECT num1, num2, sum, sum * sum as sum_sq FROM {{sum_solid.name}}'''

    sum_solid = create_templated_sql_transform_solid(
        name='sum_solid',
        sql=sum_sql_template,
        table_arguments=['sum_table'],
        dependencies=[],
        output='sum_table',
    )

    sum_sq_solid = create_templated_sql_transform_solid(
        name='sum_sq_solid',
        sql=sum_sq_sql_template,
        table_arguments=['sum_sq_table'],
        dependencies=[sum_solid],
        output='sum_sq_table',
    )

    pipeline = dagster.pipeline(solids=[sum_solid, sum_sq_solid])
    first_sum_table = 'first_sum_table'
    first_sum_sq_table = 'first_sum_sq_table'
    first_input_arg_dict = {
        'sum_table': {
            'name': first_sum_table,
        },
        'sum_sq_table': {
            'name': first_sum_sq_table,
        },
    }
    first_result = dagster.execute_pipeline(context, pipeline, first_input_arg_dict)
    assert first_result.success

    assert len(first_result.result_list) == 2
    assert first_result.result_list[0].materialized_output == {'name': first_sum_table}
    assert first_result.result_list[1].materialized_output == {'name': first_sum_sq_table}

    assert _load_table(context, first_sum_table) == [(1, 2, 3), (3, 4, 7)]

    assert _load_table(context, first_sum_sq_table) == [(1, 2, 3, 9), (3, 4, 7, 49)]

    # now execute subdag

    second_input_arg_dict = {
        'sum_solid': {
            'name': first_sum_table,
        },
        'sum_sq_table': {
            'name': 'second_sum_sq_table',
        },
    }

    second_result = dagster.execute_pipeline(
        context, pipeline, second_input_arg_dict, through_solids=['sum_sq_solid']
    )
    assert second_result.success
    assert len(second_result.result_list) == 1
    assert _load_table(context, 'second_sum_sq_table') == [(1, 2, 3, 9), (3, 4, 7, 49)]


def test_templated_sql_solid_with_api():
    context = in_mem_context()

    sql_template = '''CREATE TABLE {{sum_table.name}} AS
        SELECT num1, num2, num1 + num2 as sum FROM num_table'''

    sum_solid = create_templated_sql_transform_solid(
        name='sum_solid',
        sql=sql_template,
        table_arguments=['sum_table'],
        dependencies=[],
        output='sum_table',
    )

    pipeline = dagster.pipeline(solids=[sum_solid])

    sum_table_arg = 'specific_sum_table'
    input_arg_dict = {'sum_table': {'name': sum_table_arg}}
    result = dagster.execute_pipeline(context, pipeline, input_arg_dict)
    assert result.success

    assert _load_table(context, sum_table_arg) == [(1, 2, 3), (3, 4, 7)]


def test_multi_input():
    context = in_mem_context()

    sum_sql_template = '''CREATE TABLE {{sum_table.name}} AS
        SELECT num1, num2, num1 + num2 as sum FROM num_table'''

    mult_sql_template = '''CREATE TABLE {{mult_table.name}} AS
        SELECT num1, num2, num1 * num2 as mult FROM num_table'''

    sum_mult_join_template = '''CREATE TABLE {{sum_mult_table.name}} AS
        SELECT {{sum_solid.name}}.num1, sum, mult FROM {{sum_solid.name}}
        INNER JOIN {{mult_solid.name}} ON {{sum_solid.name}}.num1 = {{mult_solid.name}}.num1'''

    sum_solid = create_templated_sql_transform_solid(
        name='sum_solid',
        sql=sum_sql_template,
        table_arguments=['sum_table'],
        dependencies=[],
        output='sum_table',
    )

    mult_solid = create_templated_sql_transform_solid(
        name='mult_solid',
        sql=mult_sql_template,
        table_arguments=['mult_table'],
        dependencies=[],
        output='mult_table',
    )

    sum_mult_solid = create_templated_sql_transform_solid(
        name='sum_mult_solid',
        sql=sum_mult_join_template,
        table_arguments=['sum_mult_table'],
        dependencies=[sum_solid, mult_solid],
        output='sum_mult_table',
    )

    pipeline = dagster.pipeline(solids=[sum_solid, mult_solid, sum_mult_solid])

    first_sum_table = 'first_sum_table'
    first_mult_table = 'first_mult_table'
    first_sum_mult_table = 'first_sum_mult_table'

    first_input_arg_dict = {
        'sum_table': {
            'name': first_sum_table
        },
        'mult_table': {
            'name': first_mult_table
        },
        'sum_mult_table': {
            'name': first_sum_mult_table
        },
    }

    first_pipeline_result = dagster.execute_pipeline(context, pipeline, first_input_arg_dict)

    assert first_pipeline_result.success
    assert len(first_pipeline_result.result_list) == 3
    assert _load_table(context, first_sum_table) == [(1, 2, 3), (3, 4, 7)]
    assert _load_table(context, first_mult_table) == [(1, 2, 2), (3, 4, 12)]
    assert _load_table(context, first_sum_mult_table) == [(1, 3, 2), (3, 7, 12)]

    second_sum_mult_table = 'second_sum_mult_table'
    second_input_arg_dict = {
        'sum_solid': {
            'name': first_sum_table
        },
        'mult_solid': {
            'name': first_mult_table
        },
        'sum_mult_table': {
            'name': second_sum_mult_table
        },
    }

    second_pipeline_result = dagster.execute_pipeline(
        context, pipeline, second_input_arg_dict, through_solids=['sum_mult_solid']
    )

    assert second_pipeline_result.success
    assert len(second_pipeline_result.result_list) == 1
    assert _load_table(context, second_sum_mult_table) == [(1, 3, 2), (3, 7, 12)]


def test_jinja():
    templated_sql = '''SELECT * FROM {{some_table.name}}'''

    sql = _render_template_string(templated_sql, some_table={'name': 'fill_me_in'})

    assert sql == '''SELECT * FROM fill_me_in'''
