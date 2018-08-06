import dagster
from dagster import config, InputDefinition
from dagster.core.execution import execute_single_solid
from dagster.sqlalchemy_kernel.subquery_builder_experimental import (
    create_sql_statement_solid, sql_file_solid
)
from dagster.utils.test import script_relative_path

from .math_test_db import in_mem_context


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


def test_basic_isolated_sql_solid():
    context = in_mem_context()

    sql_text = '''CREATE TABLE sum_table AS SELECT num1, num2, num1 + num2 as sum FROM num_table'''

    basic_isolated_sql_solid = create_sql_statement_solid('basic_isolated_sql_solid', sql_text)

    result = execute_single_solid(
        context, basic_isolated_sql_solid, environment=config.Environment.empty()
    )

    assert result.success

    results = context.resources.sa.engine.connect().execute('SELECT * from sum_table').fetchall()
    assert results == [(1, 2, 3), (3, 4, 7)]


def test_basic_pipeline():
    sum_sql_text = '''CREATE TABLE sum_table AS
            SELECT num1, num2, num1 + num2 as sum FROM num_table'''

    sum_sq_sql_text = '''CREATE TABLE sum_sq_table AS
            SELECT num1, num2, sum, sum * sum as sum_sq FROM sum_table'''

    sum_sql_solid = create_sql_statement_solid('sum_sql_solid', sum_sql_text)

    sum_sq_sql_solid = create_sql_statement_solid(
        'sum_sq_sql_solid',
        sum_sq_sql_text,
        inputs=[InputDefinition(name=sum_sql_solid.name, depends_on=sum_sql_solid)]
    )

    pipeline = pipeline_test_def(solids=[sum_sql_solid, sum_sq_sql_solid], context=in_mem_context())

    pipeline_result = dagster.execute_pipeline(pipeline, environment=config.Environment.empty())

    assert pipeline_result.success

    exec_results = pipeline_result.result_list

    assert len(exec_results) == 2

    for exec_result in exec_results:
        assert exec_result.success is True

    engine = pipeline_result.context.resources.sa.engine

    results = engine.connect().execute('SELECT * from sum_table').fetchall()
    assert results == [(1, 2, 3), (3, 4, 7)]

    results = engine.connect().execute('SELECT * from sum_sq_table').fetchall()
    assert results == [(1, 2, 3, 9), (3, 4, 7, 49)]


def test_pipeline_from_files():
    create_sum_table_solid = sql_file_solid(script_relative_path('sql_files/create_sum_table.sql'))

    create_sum_sq_table_solid = sql_file_solid(
        script_relative_path('sql_files/create_sum_sq_table.sql'),
        inputs=[InputDefinition(create_sum_table_solid.name, depends_on=create_sum_table_solid)],
    )

    pipeline = pipeline_test_def(
        solids=[create_sum_table_solid, create_sum_sq_table_solid], context=in_mem_context()
    )

    pipeline_result = dagster.execute_pipeline(pipeline, environment=config.Environment.empty())

    assert pipeline_result.success

    exec_results = pipeline_result.result_list

    for exec_result in exec_results:
        assert exec_result.success is True

    engine = pipeline_result.context.resources.sa.engine

    results = engine.connect().execute('SELECT * from sum_table').fetchall()
    assert results == [(1, 2, 3), (3, 4, 7)]

    results = engine.connect().execute('SELECT * from sum_sq_table').fetchall()
    assert results == [(1, 2, 3, 9), (3, 4, 7, 49)]
