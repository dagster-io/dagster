import sqlalchemy as sa

import solidic
import dagster.sqlalchemy_kernel as dagster_sa


def create_engine_for_pipeline():
    engine = sa.create_engine('sqlite://')
    create_num_table(engine)
    return engine


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


def define_pipeline():
    sum_table_solid = dagster_sa.create_sql_solid(
        name='sum_table',
        inputs=[dagster_sa.create_table_input('num_table')],
        sql_text='SELECT num1, num2, num1 + num2 as sum FROM ({num_table})',
    )

    sum_sq_table_solid = dagster_sa.create_sql_solid(
        name='sum_sq_table',
        inputs=[dagster_sa.create_table_input_dependency(sum_table_solid)],
        sql_text='SELECT num1, num2, sum, sum * sum as sum_sq from ({sum_table})',
    )

    return solidic.pipeline(name='sql_hello_world', solids=[sum_table_solid, sum_sq_table_solid])
