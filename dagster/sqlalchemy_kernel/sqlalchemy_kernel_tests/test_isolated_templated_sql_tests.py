import jinja2
import dagster
from dagster import check
from dagster.core.definitions import (Solid, InputDefinition)
from .math_test_db import in_mem_context


def _render_template_string(template_text, **kwargs):
    template = jinja2.Environment(loader=jinja2.BaseLoader).from_string(template_text)
    return template.render(**kwargs)


def get_do_test_templated_sql_solid_no_api_transform(sql, input_names, output_tables):
    def do_transform(context, **kwargs):
        args = {}
        for input_name in input_names:
            args = {**args, **kwargs[input_name]}
        context.engine.connect().execute(_render_template_string(sql, **args))
        passthrough_args = {}
        for output_table in output_tables:
            passthrough_args[output_table] = args[output_table]
        return passthrough_args

    return do_transform


def _load_table(context, table_name):
    return context.engine.connect().execute(f'SELECT * FROM {table_name}').fetchall()


def test_templated_sql_solid_no_api():
    context = in_mem_context()

    sql = '''CREATE TABLE {{sum_table}} AS SELECT num1, num2, num1 + num2 as sum FROM num_table'''

    sum_table_arg = 'specific_sum_table'

    sum_solid_input_args = InputDefinition(
        name='sum_solid_input_args',
        input_fn=lambda arg_dict: arg_dict,
        argument_def_dict={'sum_table': dagster.core.types.STRING}
    )

    sum_solid = Solid(
        name='sum_solid',
        inputs=[sum_solid_input_args],
        transform_fn=get_do_test_templated_sql_solid_no_api_transform(
            sql, ['sum_solid_input_args'], ['sum_table']
        ),
        outputs=[],
    )

    pipeline = dagster.pipeline(solids=[sum_solid])

    input_arg_dict = {'sum_solid_input_args': {'sum_table': sum_table_arg}}
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


def _templated_sql_solid(name, sql_template, inputs, output_tables=None):
    check.str_param(name, 'name')
    check.str_param(sql_template, 'sql_template')
    check.list_param(inputs, 'inputs', of_type=InputDefinition)

    input_names = [input_def.name for input_def in inputs]

    return Solid(
        name=name,
        inputs=inputs,
        transform_fn=get_do_test_templated_sql_solid_no_api_transform(
            sql_template, input_names, output_tables or []
        ),
        outputs=[],
    )


def test_templated_sql_solid_with_api():
    context = in_mem_context()

    sql_template = '''CREATE TABLE {{sum_table}} AS
        SELECT num1, num2, num1 + num2 as sum FROM num_table'''

    sum_solid = _templated_sql_solid(
        name='sum_solid',
        sql_template=sql_template,
        inputs=[_args_input('sum_solid_input_args', ['sum_table'])]
    )

    pipeline = dagster.pipeline(solids=[sum_solid])

    sum_table_arg = 'specific_sum_table'
    input_arg_dict = {'sum_solid_input_args': {'sum_table': sum_table_arg}}
    result = dagster.execute_pipeline(context, pipeline, input_arg_dict)
    assert result.success

    assert _load_table(context, sum_table_arg) == [(1, 2, 3), (3, 4, 7)]


def test_templated_sql_solid_pipeline():
    context = in_mem_context()

    sum_sql_template = '''CREATE TABLE {{sum_table}} AS
        SELECT num1, num2, num1 + num2 as sum FROM num_table'''

    sum_sq_sql_template = '''CREATE TABLE {{sum_sq_table}} AS
        SELECT num1, num2, sum, sum * sum as sum_sq FROM {{sum_table}}'''

    # sum_sq_plus_sql_template = '''CREATE TABLE {{sum_sq_plus_table}} AS
    #     SELECT num1, num2, sum, sum_sq, sum_sq + 1 as sum_sq_plus FROM {{sum_sq_table}}'''

    sum_solid = _templated_sql_solid(
        name='sum_solid',
        sql_template=sum_sql_template,
        inputs=[_args_input('sum_solid_input_args', ['sum_table'])],
        output_tables=['sum_table'],
    )

    sum_sq_solid = _templated_sql_solid(
        name='sum_sq_solid',
        sql_template=sum_sq_sql_template,
        inputs=[
            _args_input('sum_solid', ['sum_table'], sum_solid),
            _args_input('sum_sq_input_args', ['sum_sq_table']),
        ],
        output_tables=['sum_sq_table'],
    )

    pipeline = dagster.pipeline(solids=[sum_solid, sum_sq_solid])
    first_sum_table = 'first_sum_table'
    first_sum_sq_table = 'first_sum_sq_table'
    first_input_arg_dict = {
        'sum_solid_input_args': {
            'sum_table': first_sum_table,
        },
        'sum_sq_input_args': {
            'sum_sq_table': first_sum_sq_table,
        },
    }
    first_result = dagster.execute_pipeline(context, pipeline, first_input_arg_dict)
    assert first_result.success

    assert len(first_result.result_list) == 2
    assert first_result.result_list[0].materialized_output == {'sum_table': first_sum_table}
    assert first_result.result_list[1].materialized_output == {'sum_sq_table': first_sum_sq_table}

    assert _load_table(context, first_sum_table) == [(1, 2, 3), (3, 4, 7)]

    assert _load_table(context, first_sum_sq_table) == [(1, 2, 3, 9), (3, 4, 7, 49)]

    # now execute subdag

    second_input_arg_dict = {
        'sum_solid': {
            'sum_table': first_sum_table,
        },
        'sum_sq_input_args': {
            'sum_sq_table': 'second_sum_sq_table',
        },
    }

    second_result = dagster.execute_pipeline(
        context, pipeline, second_input_arg_dict, through_solids=['sum_sq_solid']
    )
    assert second_result.success
    assert len(second_result.result_list) == 1
    assert _load_table(context, 'second_sum_sq_table') == [(1, 2, 3, 9), (3, 4, 7, 49)]


def test_multi_input():
    context = in_mem_context()

    sum_sql_template = '''CREATE TABLE {{sum_table}} AS
        SELECT num1, num2, num1 + num2 as sum FROM num_table'''

    mult_sql_template = '''CREATE TABLE {{mult_table}} AS
        SELECT num1, num2, num1 * num2 as mult FROM num_table'''

    sum_mutl_join_template = '''CREATE TABLE {{sum_mult_table}} AS
        SELECT {{sum_table}}.num1, sum, mult FROM {{sum_table}}
        INNER JOIN {{mult_table}} ON {{sum_table}}.num1 = {{mult_table}}.num1'''

    sum_solid = _templated_sql_solid(
        name='sum_solid',
        sql_template=sum_sql_template,
        inputs=[_args_input('sum_solid_input_args', ['sum_table'])],
        output_tables=['sum_table']
    )

    mult_solid = _templated_sql_solid(
        name='mult_solid',
        sql_template=mult_sql_template,
        inputs=[_args_input('mult_solid_input_args', ['mult_table'])],
        output_tables=['mult_table']
    )

    sum_mult_solid = _templated_sql_solid(
        name='sum_mult_solid',
        sql_template=sum_mutl_join_template,
        inputs=[
            _args_input('sum_mult_solid_input_args', ['sum_mult_table']),
            _args_input('sum_solid', ['sum_table'], depends_on=sum_solid),
            _args_input('mult_solid', ['mult_table'], depends_on=mult_solid),
        ],
        output_tables=['sum_mult_table']
    )

    pipeline = dagster.pipeline(solids=[sum_solid, mult_solid, sum_mult_solid])

    first_sum_table = 'first_sum_table'
    first_mult_table = 'first_mult_table'
    first_sum_mult_table = 'first_sum_mult_table'

    first_input_arg_dict = {
        'sum_solid_input_args': {
            'sum_table': first_sum_table
        },
        'mult_solid_input_args': {
            'mult_table': first_mult_table
        },
        'sum_mult_solid_input_args': {
            'sum_mult_table': first_sum_mult_table
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
            'sum_table': first_sum_table
        },
        'mult_solid': {
            'mult_table': first_mult_table
        },
        'sum_mult_solid_input_args': {
            'sum_mult_table': second_sum_mult_table
        },
    }

    second_pipeline_result = dagster.execute_pipeline(
        context, pipeline, second_input_arg_dict, through_solids=['sum_mult_solid']
    )

    assert second_pipeline_result.success
    assert len(second_pipeline_result.result_list) == 1
    assert _load_table(context, second_sum_mult_table) == [(1, 3, 2), (3, 7, 12)]


def test_jinja():
    templated_sql = '''SELECT * FROM {{some_table}}'''

    sql = _render_template_string(templated_sql, some_table='fill_me_in')

    assert sql == '''SELECT * FROM fill_me_in'''
