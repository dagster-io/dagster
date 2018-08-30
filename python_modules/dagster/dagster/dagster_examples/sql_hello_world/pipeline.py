import sqlalchemy as sa

from dagster import (
    DependencyDefinition,
    PipelineDefinition,
)

from dagster.sqlalchemy.subquery_builder_experimental import (
    create_sql_solid,
    create_table_expression_input,
)


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
    sum_table_solid = create_sql_solid(
        name='sum_table',
        inputs=[create_table_expression_input('num_table')],
        sql_text='SELECT num1, num2, num1 + num2 as sum FROM ({num_table})',
    )

    sum_sq_table_solid = create_sql_solid(
        name='sum_sq_table',
        inputs=[create_table_expression_input(sum_table_solid)],
        sql_text='SELECT num1, num2, sum, sum * sum as sum_sq from ({sum_table})',
    )

    return PipelineDefinition(
        name='sql_hello_world',
        solids=[sum_table_solid, sum_sq_table_solid],
        dependencies={
            sum_sq_table_solid.name: {
                sum_table_solid.name: DependencyDefinition(sum_table_solid.name)
            }
        },
    )
