import sqlalchemy as sa

from dagster import (
    DependencyDefinition,
    InputDefinition,
    PipelineContextDefinition,
    PipelineDefinition,
    check,
    config,
    execute_pipeline,
)

from dagster.core.utility_solids import define_pass_mem_value

from dagster.sqlalchemy_kernel.subquery_builder_experimental import (
    create_sql_solid,
    DagsterSqlTableExpression,
)
from .math_test_db import in_mem_context


def pipeline_test_def(solids, context, dependencies):
    return PipelineDefinition(
        solids=solids,
        context_definitions={
            'default':
            PipelineContextDefinition(
                argument_def_dict={},
                context_fn=lambda _pipeline, _args: context,
            ),
        },
        dependencies=dependencies,
    )


def create_num_table(engine):
    metadata = sa.MetaData(engine)

    table = sa.Table(
        'num_table',
        metadata,
        sa.Column('num1', sa.Integer),
        sa.Column('num2', sa.Integer),
    )

    table.create()

    conn = engine.connect()

    conn.execute('''INSERT INTO num_table VALUES(1, 2)''')
    conn.execute('''INSERT INTO num_table VALUES(3, 4)''')


def test_sql_sum_solid():
    expr_solid = define_pass_mem_value('expr', DagsterSqlTableExpression('num_table'))

    sum_table_solid = create_sum_table_solid()

    environment = config.Environment(
        materializations=[
            config.Materialization(
                solid='sum_table',
                name='CREATE',
                args={'table_name': 'sum_table'},
            )
        ],
    )

    pipeline = pipeline_test_def(
        solids=[expr_solid, sum_table_solid],
        context=in_mem_context(),
        dependencies={'sum_table': {
            'num_table': DependencyDefinition('expr')
        }},
    )

    pipeline_result = execute_pipeline(pipeline, environment)
    assert pipeline_result.success

    result = pipeline_result.result_named(sum_table_solid.name)

    assert result.success

    results = result.context.resources.sa.engine.connect().execute('SELECT * FROM sum_table'
                                                                   ).fetchall()
    assert results == [(1, 2, 3), (3, 4, 7)]


def create_sum_table_solid():
    return create_sql_solid(
        name='sum_table',
        inputs=[InputDefinition('num_table')],
        sql_text='SELECT num1, num2, num1 + num2 as sum FROM {num_table}',
    )


def create_sum_sq_pipeline(context, expr):
    check.inst_param(expr, 'expr', DagsterSqlTableExpression)

    expr_solid = define_pass_mem_value('expr', expr)

    sum_solid = create_sum_table_solid()

    sum_sq_solid = create_sql_solid(
        name='sum_sq_table',
        inputs=[InputDefinition(sum_solid.name)],
        sql_text='SELECT num1, num2, sum, sum * sum as sum_sq from {sum_table}',
    )

    return pipeline_test_def(
        solids=[expr_solid, sum_solid, sum_sq_solid],
        context=context,
        dependencies={
            sum_solid.name: {
                'num_table': DependencyDefinition('expr'),
            },
            sum_sq_solid.name: {
                sum_solid.name: DependencyDefinition(sum_solid.name),
            },
        },
    )


def test_execute_sql_sum_sq_solid():
    pipeline = create_sum_sq_pipeline(in_mem_context(), DagsterSqlTableExpression('num_table'))

    environment = config.Environment()

    pipeline_result = execute_pipeline(
        pipeline,
        environment=environment,
    )

    assert pipeline_result.success

    result_list = pipeline_result.result_list

    sum_table_sql_text = result_list[1].transformed_value.query_text
    assert sum_table_sql_text == 'SELECT num1, num2, num1 + num2 as sum FROM num_table'

    sum_sq_table_sql_text = result_list[2].transformed_value.query_text
    assert sum_sq_table_sql_text == 'SELECT num1, num2, sum, sum * sum as sum_sq from ' + \
            '(SELECT num1, num2, num1 + num2 as sum FROM num_table)'


def test_output_sql_sum_sq_solid():
    pipeline = create_sum_sq_pipeline(in_mem_context(), DagsterSqlTableExpression('num_table'))

    environment = config.Environment(
        materializations=[
            config.Materialization(
                solid='sum_sq_table',
                name='CREATE',
                args={'table_name': 'sum_sq_table'},
            )
        ],
    )

    pipeline_result = execute_pipeline(pipeline=pipeline, environment=environment)

    assert pipeline_result.success

    result_list = pipeline_result.result_list

    assert len(result_list) == 3
    engine = pipeline_result.context.resources.sa.engine
    result_list = engine.connect().execute('SELECT * FROM sum_sq_table').fetchall()
    assert result_list == [(1, 2, 3, 9), (3, 4, 7, 49)]
