import pandas as pd

from dagster import check

from dagster.core.definitions import (
    SolidDefinition,
    InputDefinition,
    MaterializationDefinition,
    OutputDefinition,
    SourceDefinition,
    ArgumentDefinition,
)
from dagster.core.errors import DagsterInvariantViolationError

from dagster.core.execution import ExecutionContext

from dagster.core import types


def parquet_dataframe_source(**read_parquet_kwargs):
    def callback(context, arg_dict):
        check.inst_param(context, 'context', ExecutionContext)
        check.str_param(arg_dict['path'], 'path')
        df = pd.read_parquet(arg_dict['path'], **read_parquet_kwargs)
        context.metric('rows', df.shape[0])
        return df

    return SourceDefinition(
        source_type='PARQUET',
        source_fn=callback,
        argument_def_dict={
            'path': ArgumentDefinition(types.Path),
        },
    )


def csv_dataframe_source(name=None, **read_csv_kwargs):
    def callback(context, arg_dict):
        check.inst_param(context, 'context', ExecutionContext)
        check.str_param(arg_dict['path'], 'path')
        df = pd.read_csv(arg_dict['path'], **read_csv_kwargs)
        context.metric('rows', df.shape[0])
        return df

    return SourceDefinition(
        source_type=check.opt_str_param(name, 'name', 'CSV'),
        source_fn=callback,
        argument_def_dict={
            'path': ArgumentDefinition(types.Path),
        },
    )


def table_dataframe_source(**read_table_kwargs):
    def callback(context, arg_dict):
        check.inst_param(context, 'context', ExecutionContext)
        path = check.str_elem(arg_dict, 'path')
        df = pd.read_table(path, **read_table_kwargs)
        context.metric('rows', df.shape[0])
        return df

    return SourceDefinition(
        source_type='TABLE',
        source_fn=callback,
        argument_def_dict={
            'path': ArgumentDefinition(types.Path),
        },
    )


def _dataframe_input_callback(_context, result):
    if not isinstance(result, pd.DataFrame):
        raise DagsterInvariantViolationError(
            f'Input source of dataframe solid ' + \
            f"did not return a dataframe. Got '{repr(result)}'"
        )


def dataframe_dependency(solid, name=None, sources=None):
    check.inst_param(solid, 'solid', SolidDefinition)

    if sources is None:
        sources = [parquet_dataframe_source(), csv_dataframe_source(), table_dataframe_source()]

    if name is None:
        name = solid.name

    return InputDefinition(name=name, sources=sources, depends_on=solid)


def dataframe_input(name, sources=None, depends_on=None, expectations=None, input_callback=None):
    check.opt_inst_param(depends_on, 'depends_on', SolidDefinition)

    if sources is None:
        sources = [parquet_dataframe_source(), csv_dataframe_source(), table_dataframe_source()]

    def callback(context, output):
        _dataframe_input_callback(context, output)
        if input_callback:
            input_callback(context, output)

    return InputDefinition(
        name=name,
        sources=sources,
        depends_on=depends_on,
        input_callback=callback,
        expectations=expectations
    )


def dataframe_csv_materialization():
    def to_csv_fn(context, arg_dict, df):
        check.inst_param(df, 'df', pd.DataFrame)
        check.inst_param(context, 'context', ExecutionContext)
        check.dict_param(arg_dict, 'arg_dict')
        path = check.str_elem(arg_dict, 'path')

        df.to_csv(path, index=False)

    return MaterializationDefinition(
        name='CSV',
        materialization_fn=to_csv_fn,
        argument_def_dict={'path': ArgumentDefinition(types.Path)},
    )


def dataframe_parquet_materialization():
    def to_parquet_fn(context, arg_dict, df):
        check.inst_param(df, 'df', pd.DataFrame)
        check.inst_param(context, 'context', ExecutionContext)
        check.dict_param(arg_dict, 'arg_dict')
        path = check.str_elem(arg_dict, 'path')

        df.to_parquet(path)

    return MaterializationDefinition(
        name='PARQUET',
        materialization_fn=to_parquet_fn,
        argument_def_dict={'path': ArgumentDefinition(types.Path)},
    )


def _dataframe_output_callback(context, result):
    if not isinstance(result, pd.DataFrame):
        raise DagsterInvariantViolationError(
            f'Trasform of dataframe solid ' + \
            f"did not return a dataframe. Got '{repr(result)}'"
        )
    context.metric('rows', result.shape[0])


def dataframe_output(materializations=None, expectations=None, output_callback=None):
    if materializations is None:
        materializations = [dataframe_csv_materialization(), dataframe_parquet_materialization()]

    def callback(context, output):
        _dataframe_output_callback(context, output)
        if output_callback:
            output_callback(context, output)

    return OutputDefinition(
        materializations=materializations,
        expectations=expectations,
        output_callback=callback,
    )
