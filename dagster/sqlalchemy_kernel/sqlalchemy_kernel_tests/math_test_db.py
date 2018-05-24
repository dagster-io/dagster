import sqlalchemy as sa
import dagster.sqlalchemy_kernel as dagster_sa


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


def in_mem_engine():
    engine = sa.create_engine('sqlite://')
    create_num_table(engine)
    return engine


def in_mem_context():
    return dagster_sa.DagsterSqlAlchemyExecutionContext(engine=in_mem_engine())
