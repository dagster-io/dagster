import os

from dagster import (
    ConfigDefinition,
    Field,
    InputDefinition,
    OutputDefinition,
    SolidDefinition,
    check,
    types,
)

from dagster.core.test_utils import single_output_transform

from dagster.sqlalchemy import execute_sql_text_on_context


class DagsterSqlExpression(object):
    @property
    def from_target(self):
        check.not_implemented('must implemented in subclass')


class DagsterSqlQueryExpression(DagsterSqlExpression):
    def __init__(self, subquery_text):
        super(DagsterSqlQueryExpression, self).__init__()
        self._subquery_text = check.str_param(subquery_text, 'subquery_text')

    @property
    def query_text(self):
        return self._subquery_text

    @property
    def from_target(self):
        return '({subquery_text})'.format(subquery_text=self._subquery_text)


class DagsterSqlTableExpression(DagsterSqlExpression):
    def __init__(self, table_name):
        super(DagsterSqlTableExpression, self).__init__()
        self._table_name = check.str_param(table_name, 'table_name')

    @property
    def query_text(self):
        check.not_implemented('table cannot be a standalone query')

    @property
    def from_target(self):
        return self._table_name


def define_create_table_solid(name):
    def _materialization_fn(info, inputs):
        sql_expr = inputs['expr']
        check.inst(sql_expr, DagsterSqlExpression)
        output_table_name = check.str_elem(info.config, 'table_name')
        total_sql = '''CREATE TABLE {output_table_name} AS {query_text}'''.format(
            output_table_name=output_table_name, query_text=sql_expr.query_text
        )
        info.context.resources.sa.engine.connect().execute(total_sql)

    return SolidDefinition(
        name=name,
        inputs=[InputDefinition('expr')],
        outputs=[],
        transform_fn=_materialization_fn,
        config_def=ConfigDefinition.config_dict({
            'table_name': Field(types.String),
        }),
    )


def _table_name_read_fn(_context, arg_dict):
    check.dict_param(arg_dict, 'arg_dict')

    table_name = check.str_elem(arg_dict, 'table_name')
    # probably verify that the table name exists?
    return DagsterSqlTableExpression(table_name)


def create_sql_transform(sql_text):
    def transform_fn(_context, inputs):
        sql_texts = {}
        for name, sql_expr in inputs.items():
            sql_texts[name] = sql_expr.from_target

        return DagsterSqlQueryExpression(sql_text.format(**sql_texts))

    return transform_fn


def create_sql_solid(name, inputs, sql_text):
    check.str_param(name, 'name')
    check.list_param(inputs, 'inputs', of_type=InputDefinition)
    check.str_param(sql_text, 'sql_text')

    return single_output_transform(
        name,
        inputs=inputs,
        transform_fn=create_sql_transform(sql_text),
        output=OutputDefinition(),
    )


def _create_sql_alchemy_transform_fn(sql_text):
    check.str_param(sql_text, 'sql_text')

    def transform_fn(context, _args):
        return execute_sql_text_on_context(context, sql_text)

    return transform_fn


def create_sql_statement_solid(name, sql_text, inputs=None):
    check.str_param(name, 'name')
    check.str_param(sql_text, 'sql_text')
    check.opt_list_param(inputs, 'inputs', of_type=InputDefinition)

    if inputs is None:
        inputs = []

    return single_output_transform(
        name=name,
        transform_fn=_create_sql_alchemy_transform_fn(sql_text),
        inputs=inputs,
        output=OutputDefinition()
    )


def sql_file_solid(path, inputs=None):
    check.str_param(path, 'path')
    check.opt_list_param(inputs, 'inputs', of_type=InputDefinition)

    basename = os.path.basename(path)
    name = os.path.splitext(basename)[0]

    with open(path, 'r') as ff:
        return create_sql_statement_solid(name, ff.read(), inputs)
