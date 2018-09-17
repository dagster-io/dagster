import sqlalchemy as sa
import dagster.sqlalchemy as dagster_sa


def create_num_table(engine, num_table_name='num_table'):
    metadata = sa.MetaData(engine)

    table = sa.Table(
        num_table_name,
        metadata,
        sa.Column('num1', sa.Integer),
        sa.Column('num2', sa.Integer),
    )

    table.create()

    conn = engine.connect()

    conn.execute(
        '''INSERT INTO {num_table_name} VALUES(1, 2)'''.format(num_table_name=num_table_name)
    )
    conn.execute(
        '''INSERT INTO {num_table_name} VALUES(3, 4)'''.format(num_table_name=num_table_name)
    )


def in_mem_engine(num_table_name='num_table'):
    engine = sa.create_engine('sqlite://')
    create_num_table(engine, num_table_name)
    return engine


def in_mem_context(num_table_name='num_table'):
    return dagster_sa.create_sql_alchemy_context_from_engine(engine=in_mem_engine(num_table_name))
