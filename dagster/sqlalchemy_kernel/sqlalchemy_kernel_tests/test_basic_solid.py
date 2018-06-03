import sqlalchemy as sa
from dagster import config
from dagster.core.execution import (
    output_single_solid, DagsterPipeline, execute_pipeline, materialize_pipeline,
    create_single_solid_env_from_arg_dicts, create_pipeline_env_from_arg_dicts
)

from dagster.sqlalchemy_kernel import DagsterSqlAlchemyExecutionContext
from dagster.sqlalchemy_kernel.subquery_builder_experimental import (
    create_sql_solid,
    create_table_expression_input,
    create_table_input_dependency,
)
from .math_test_db import in_mem_engine


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
    sum_table_solid = create_sum_table_solid()

    engine = sa.create_engine('sqlite://')
    create_num_table(engine)

    input_arg_dicts = {'num_table': {'table_name': 'num_table'}}

    result = output_single_solid(
        DagsterSqlAlchemyExecutionContext(engine=engine),
        sum_table_solid,
        environment=create_single_solid_env_from_arg_dicts(sum_table_solid, input_arg_dicts),
        materialization_type='CREATE',
        arg_dict={'table_name': 'sum_table'},
    )
    assert result.success

    results = engine.connect().execute('SELECT * FROM sum_table').fetchall()
    assert results == [(1, 2, 3), (3, 4, 7)]


def create_sum_table_solid():
    return create_sql_solid(
        name='sum_table',
        inputs=[create_table_expression_input('num_table')],
        sql_text='SELECT num1, num2, num1 + num2 as sum FROM {num_table}',
    )


def create_sum_sq_pipeline():
    sum_solid = create_sum_table_solid()

    sum_sq_solid = create_sql_solid(
        name='sum_sq_table',
        inputs=[create_table_input_dependency(sum_solid)],
        sql_text='SELECT num1, num2, sum, sum * sum as sum_sq from {sum_table}',
    )

    pipeline = DagsterPipeline(solids=[sum_solid, sum_sq_solid])
    return pipeline


def test_execute_sql_sum_sq_solid():
    pipeline = create_sum_sq_pipeline()

    engine = in_mem_engine()

    pipeline_result = execute_pipeline(
        DagsterSqlAlchemyExecutionContext(engine=engine),
        pipeline,
        environment=create_pipeline_env_from_arg_dicts(
            pipeline, {'num_table': {
                'table_name': 'num_table'
            }}
        ),
    )

    assert pipeline_result.success

    result_list = pipeline_result.result_list

    sum_table_sql_text = result_list[0].transformed_value.query_text
    assert sum_table_sql_text == 'SELECT num1, num2, num1 + num2 as sum FROM num_table'

    sum_sq_table_sql_text = result_list[1].transformed_value.query_text
    assert sum_sq_table_sql_text == 'SELECT num1, num2, sum, sum * sum as sum_sq from ' + \
            '(SELECT num1, num2, num1 + num2 as sum FROM num_table)'


def test_output_sql_sum_sq_solid():
    pipeline = create_sum_sq_pipeline()
    engine = sa.create_engine('sqlite://')
    create_num_table(engine)
    engine = in_mem_engine()

    pipeline_result = materialize_pipeline(
        DagsterSqlAlchemyExecutionContext(engine=engine),
        pipeline,
        environment=create_pipeline_env_from_arg_dicts(
            pipeline, {'num_table': {
                'table_name': 'num_table'
            }}
        ),
        materializations=[
            config.Materialization(
                solid='sum_sq_table',
                materialization_type='CREATE',
                args={'table_name': 'sum_sq_table'},
            )
        ],
    )

    assert pipeline_result.success

    result_list = pipeline_result.result_list

    assert len(result_list) == 2
    result_list = engine.connect().execute('SELECT * FROM sum_sq_table').fetchall()
    assert result_list == [(1, 2, 3, 9), (3, 4, 7, 49)]
