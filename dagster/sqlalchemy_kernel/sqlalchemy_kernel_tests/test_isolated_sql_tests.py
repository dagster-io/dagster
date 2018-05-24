import dagster
from dagster.transform_only_solid import (dep_only_input, no_args_transform_solid)
from dagster.core.definitions import (Solid, InputDefinition)
from dagster.core.execution import execute_single_solid
import dagster.sqlalchemy_kernel as dagster_sa

from .math_test_db import in_mem_engine


def create_sql_alchemy_transform_fn(sql_text):
    def transform_fn(context):
        context.engine.connect().execute(sql_text)

    return transform_fn


def create_sql_statement_solid(name, sql_text):
    return no_args_transform_solid(
        name,
        no_args_transform_fn=create_sql_alchemy_transform_fn(sql_text),
    )


def test_basic_isolated_sql_solid():
    engine = in_mem_engine()

    sql_text = '''CREATE TABLE sum_table AS SELECT num1, num2, num1 + num2 as sum FROM num_table'''

    basic_isolated_sql_solid = create_sql_statement_solid('basic_isolated_sql_solid', sql_text)

    execute_single_solid(
        dagster_sa.DagsterSqlAlchemyExecutionContext(engine=engine),
        basic_isolated_sql_solid,
        input_arg_dicts={},
        throw_on_error=True,
    )

    results = engine.connect().execute('SELECT * from sum_table').fetchall()
    assert results == [(1, 2, 3), (3, 4, 7)]
