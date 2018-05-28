from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *  # pylint: disable=W0622,W0401

import os

import sqlalchemy as sa

from dagster import check

import dagster.core
from dagster.core import types
from dagster.core.execution import (DagsterExecutionContext)
from dagster.core.definitions import (Solid, InputDefinition, OutputDefinition)
from dagster.transform_only_solid import (dep_only_input, no_args_transform_solid)

from .templated import execute_sql_text_on_context
from .common import DagsterSqlAlchemyExecutionContext


class DagsterSqlExpression:
    @property
    def from_target(self):
        check.not_implemented('must implemented in subclass')


class DagsterSqlQueryExpression(DagsterSqlExpression):
    def __init__(self, subquery_text):
        super().__init__()
        self._subquery_text = check.str_param(subquery_text, 'subquery_text')

    @property
    def query_text(self):
        return self._subquery_text

    @property
    def from_target(self):
        return f'({self._subquery_text})'


class DagsterSqlTableExpression(DagsterSqlExpression):
    def __init__(self, table_name):
        super().__init__()
        self._table_name = check.str_param(table_name, 'table_name')

    @property
    def query_text(self):
        check.not_implemented('table cannot be a standalone query')

    @property
    def from_target(self):
        return self._table_name


def create_table_output():
    def output_fn(sql_expr, context, arg_dict):
        check.inst_param(sql_expr, 'sql_expr', DagsterSqlExpression)
        check.inst_param(context, 'context', DagsterSqlAlchemyExecutionContext)
        check.dict_param(arg_dict, 'arg_dict')

        output_table_name = check.str_elem(arg_dict, 'table_name')
        total_sql = '''CREATE TABLE {output_table_name} AS {query_text}'''.format(
            output_table_name=output_table_name, query_text=sql_expr.query_text
        )
        context.engine.connect().execute(total_sql)

    return OutputDefinition(
        name='CREATE',
        output_fn=output_fn,
        argument_def_dict={'table_name': types.STRING},
    )


def truncate_and_insert_table_output():
    def output_fn(sql_expr, context, arg_dict):
        check.inst_param(sql_expr, 'sql_expr', DagsterSqlExpression)
        check.inst_param(context, 'context', DagsterSqlAlchemyExecutionContext)
        check.dict_param(arg_dict, 'arg_dict')

        output_table_name = check.str_elem(arg_dict, 'table_name')
        total_sql = '''TRUNCATE TABLE {output_table_name}; INSERT INTO {output_table_name} ({sql_text})'''.format(
            output_table_name=output_table_name, sql_text=sql_expr.sql_text
        )
        print(total_sql)
        context.engine.connect().execute(total_sql)

    return OutputDefinition(
        name='TRUNCATE_AND_INSERT',
        output_fn=output_fn,
        argument_def_dict={'table_name': types.STRING},
    )


def _table_input_fn(context, arg_dict):

    check.inst_param(context, 'context', DagsterSqlAlchemyExecutionContext)
    check.dict_param(arg_dict, 'arg_dict')

    table_name = check.str_elem(arg_dict, 'table_name')
    # probably verify that the table name exists?
    return DagsterSqlTableExpression(table_name)


def create_table_input(name):
    check.str_param(name, 'name')

    return InputDefinition(
        name=name, input_fn=_table_input_fn, argument_def_dict={
            'table_name': types.STRING,
        }
    )


def create_table_input_dependency(solid):
    check.inst_param(solid, 'solid', Solid)

    return InputDefinition(
        name=solid.name,
        input_fn=_table_input_fn,
        argument_def_dict={
            'table_name': types.STRING,
        },
        depends_on=solid
    )


def create_sql_transform(sql_text):
    def transform_fn(**kwargs):
        sql_texts = {}
        for name, sql_expr in kwargs.items():
            if name == 'context':
                continue

            sql_texts[name] = sql_expr.from_target

        return DagsterSqlQueryExpression(sql_text.format(**sql_texts))

    return transform_fn


def create_sql_solid(name, inputs, sql_text):
    check.str_param(name, 'name')
    check.list_param(inputs, 'inputs', of_type=InputDefinition)
    check.str_param(sql_text, 'sql_text')

    return Solid(
        name,
        inputs=inputs,
        transform_fn=create_sql_transform(sql_text),
        outputs=[create_table_output(), truncate_and_insert_table_output()],
    )


def _create_sql_alchemy_transform_fn(sql_text):
    check.str_param(sql_text, 'sql_text')

    def transform_fn(context):
        return execute_sql_text_on_context(context, sql_text)

    return transform_fn


def create_sql_statement_solid(name, sql_text, inputs=None):
    check.str_param(name, 'name')
    check.str_param(sql_text, 'sql_text')
    check.opt_list_param(inputs, 'inputs', of_type=InputDefinition)
    return no_args_transform_solid(
        name,
        no_args_transform_fn=_create_sql_alchemy_transform_fn(sql_text),
        inputs=inputs,
    )


def sql_file_solid(path, inputs=None):
    check.str_param(path, 'path')
    check.opt_list_param(inputs, 'inputs', of_type=InputDefinition)

    basename = os.path.basename(path)
    name = os.path.splitext(basename)[0]

    with open(path, 'r') as ff:
        return create_sql_statement_solid(name, ff.read(), inputs)
