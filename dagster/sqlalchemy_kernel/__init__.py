from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *  # pylint: disable=W0622,W0401

import sqlalchemy as sa

from dagster import check

import dagster.core
from dagster.core.execution import (DagsterExecutionContext)
from dagster.core.definitions import (Solid, SolidInputDefinition, SolidOutputDefinition)


class DagsterSqlAlchemyExecutionContext(DagsterExecutionContext):
    def __init__(self, engine, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.engine = check.inst_param(engine, 'engine', sa.engine.Engine)


class DagsterSqlExpression:
    def __init__(self, sql_text):
        self.sql_text = check.str_param(sql_text, 'sql_text')


def create_table_output():
    def output_fn(sql_expr, context, arg_dict):
        check.inst_param(sql_expr, 'sql_expr', DagsterSqlExpression)
        check.inst_param(context, 'context', DagsterSqlAlchemyExecutionContext)
        check.dict_param(arg_dict, 'arg_dict')

        output_table_name = check.str_elem(arg_dict, 'table_name')
        total_sql = '''CREATE TABLE {output_table_name} AS {sql_text}'''.format(
            output_table_name=output_table_name, sql_text=sql_expr.sql_text
        )
        context.engine.connect().execute(total_sql)

    return SolidOutputDefinition(
        name='CREATE',
        output_fn=output_fn,
        argument_def_dict={'table_name': dagster.core.types.SolidString},
    )


def _table_input_fn(context, arg_dict):

    check.inst_param(context, 'context', DagsterSqlAlchemyExecutionContext)
    check.dict_param(arg_dict, 'arg_dict')

    table_name = check.str_elem(arg_dict, 'table_name')
    # probably verify that the table name exists?
    return DagsterSqlExpression(table_name)


def create_table_input(name):
    check.str_param(name, 'name')

    return SolidInputDefinition(
        name=name,
        input_fn=_table_input_fn,
        argument_def_dict={
            'table_name': dagster.core.types.SolidString,
        }
    )


def create_table_input_dependency(solid):
    check.inst_param(solid, 'solid', Solid)

    return SolidInputDefinition(
        name=solid.name,
        input_fn=_table_input_fn,
        argument_def_dict={
            'table_name': dagster.core.types.SolidString,
        },
        depends_on=solid
    )


def create_sql_transform(sql_text):
    def transform_fn(**kwargs):
        sql_texts = {}
        for name, sql_expr in kwargs.items():
            if name == 'context':
                continue

            sql_texts[name] = sql_expr.sql_text

        return DagsterSqlExpression(sql_text.format(**sql_texts))

    return transform_fn


def create_sql_solid(name, inputs, sql_text):
    check.str_param(name, 'name')
    check.list_param(inputs, 'inputs', of_type=SolidInputDefinition)
    check.str_param(sql_text, 'sql_text')

    return Solid(
        name,
        inputs=inputs,
        transform_fn=create_sql_transform(sql_text),
        outputs=[create_table_output()],
    )
