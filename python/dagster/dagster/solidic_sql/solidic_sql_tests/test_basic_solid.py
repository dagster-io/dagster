import sqlalchemy as sa
from solidic.execution import (
    output_single_solid, SolidPipeline, execute_pipeline, output_pipeline
)

from dagster import solidic_sql


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
        solidic_sql.SolidicSqlExecutionContext(engine=engine),
        sum_table_solid,
        input_arg_dicts,
        'CREATE', {'table_name': 'sum_table'}
    )
    assert result.success

    results = engine.connect().execute('SELECT * FROM sum_table').fetchall()
    assert results == [(1, 2, 3), (3, 4, 7)]


def create_sum_table_solid():
    return solidic_sql.create_sql_solid(
        name='sum_table',
        inputs=[solidic_sql.create_table_input('num_table')],
        sql_text='SELECT num1, num2, num1 + num2 as sum FROM ({num_table})',
    )


def create_sum_sq_pipeline():
    sum_solid = create_sum_table_solid()

    sum_sq_solid = solidic_sql.create_sql_solid(
        name='sum_sq_table',
        inputs=[solidic_sql.create_table_input_dependency(sum_solid)],
        sql_text='SELECT num1, num2, sum, sum * sum as sum_sq from ({sum_table})',
    )

    pipeline = SolidPipeline(solids=[sum_solid, sum_sq_solid])
    return pipeline


def test_execute_sql_sum_sq_solid():
    pipeline = create_sum_sq_pipeline()
    engine = sa.create_engine('sqlite://')
    create_num_table(engine)

    results = execute_pipeline(
        solidic_sql.SolidicSqlExecutionContext(engine=engine),
        pipeline,
        input_arg_dicts={'num_table': {
            'table_name': 'num_table'
        }},
        throw_on_error=True,
    )

    sum_table_sql_text = results[0].materialized_output.sql_text
    assert sum_table_sql_text == 'SELECT num1, num2, num1 + num2 as sum FROM (num_table)'

    sum_sq_table_sql_text = results[1].materialized_output.sql_text
    assert sum_sq_table_sql_text == 'SELECT num1, num2, sum, sum * sum as sum_sq from ' + \
            '(SELECT num1, num2, num1 + num2 as sum FROM (num_table))'


def test_output_sql_sum_sq_solid():
    pipeline = create_sum_sq_pipeline()
    engine = sa.create_engine('sqlite://')
    create_num_table(engine)

    sum_sq_output_arg_dicts = {'sum_sq_table': {'CREATE': {'table_name': 'sum_sq_table'}}}

    results = output_pipeline(
        solidic_sql.SolidicSqlExecutionContext(engine=engine),
        pipeline,
        input_arg_dicts={'num_table': {
            'table_name': 'num_table'
        }},
        output_arg_dicts=sum_sq_output_arg_dicts,
        throw_on_error=True,
    )

    assert len(results) == 2
    results = engine.connect().execute('SELECT * FROM sum_sq_table').fetchall()
    assert results == [(1, 2, 3, 9), (3, 4, 7, 49)]
