import sqlalchemy as sa

from dagster.sqlalchemy.common import (
    DefaultSqlAlchemyResources,
    SqlAlchemyResource,
    check_supports_sql_alchemy_resource,
    create_sql_alchemy_context_params_from_engine,
)

from dagster.utils.test import create_test_runtime_execution_context


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


def create_sql_alchemy_context_from_engine(engine, *args, **kwargs):
    resources = DefaultSqlAlchemyResources(SqlAlchemyResource(engine))
    context = create_test_runtime_execution_context(resources=resources, *args, **kwargs)
    return check_supports_sql_alchemy_resource(context)


def in_mem_context(num_table_name='num_table'):
    return create_sql_alchemy_context_from_engine(engine=in_mem_engine(num_table_name))


def in_mem_context_params(num_table_name='num_table'):
    return create_sql_alchemy_context_params_from_engine(engine=in_mem_engine(num_table_name))
