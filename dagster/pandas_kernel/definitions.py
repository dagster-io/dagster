import pandas as pd

from dagster import check

from dagster.core.definitions import (
    Solid, create_dagster_single_file_input, InputDefinition, create_single_source_input,
    MaterializationDefinition, OutputDefinition, SourceDefinition
)
from dagster.core.execution import DagsterExecutionContext

from dagster.core import types


def parquet_dataframe_source(**read_parquet_kwargs):
    def callback(context, arg_dict):
        check.inst_param(context, 'context', DagsterExecutionContext)
        check.str_param(arg_dict['path'], 'path')
        df = pd.read_parquet(arg_dict['path'], **read_parquet_kwargs)
        context.metric('rows', df.shape[0])
        return df

    return SourceDefinition(
        source_type='PARQUET',
        source_fn=callback,
        argument_def_dict={
            'path': types.PATH,
        },
    )


def csv_dataframe_source(**read_csv_kwargs):
    def callback(context, arg_dict):
        check.inst_param(context, 'context', DagsterExecutionContext)
        check.str_param(arg_dict['path'], 'path')
        df = pd.read_csv(arg_dict['path'], **read_csv_kwargs)
        context.metric('rows', df.shape[0])
        return df

    return SourceDefinition(
        source_type='CSV',
        source_fn=callback,
        argument_def_dict={
            'path': types.PATH,
        },
    )


def table_dataframe_source(**read_table_kwargs):
    def callback(context, arg_dict):
        check.inst_param(context, 'context', DagsterExecutionContext)
        path = check.str_elem(arg_dict, 'path')
        df = pd.read_table(path, **read_table_kwargs)
        context.metric('rows', df.shape[0])
        return df

    return SourceDefinition(
        source_type='TABLE',
        source_fn=callback,
        argument_def_dict={
            'path': types.PATH,
        },
    )


def dataframe_dependency(solid, name=None, sources=None):
    check.inst_param(solid, 'solid', Solid)

    if sources is None:
        sources = [parquet_dataframe_source(), csv_dataframe_source(), table_dataframe_source()]

    if name is None:
        name = solid.name

    return InputDefinition(name=name, sources=sources, depends_on=solid)


def dataframe_input(name, sources=None):
    if sources is None:
        sources = [parquet_dataframe_source(), csv_dataframe_source(), table_dataframe_source()]

    return InputDefinition(name=name, sources=sources)


def dataframe_csv_materialization():
    def to_csv_fn(df, context, arg_dict):
        check.inst_param(df, 'df', pd.DataFrame)
        check.inst_param(context, 'context', DagsterExecutionContext)
        check.dict_param(arg_dict, 'arg_dict')
        path = check.str_elem(arg_dict, 'path')

        df.to_csv(path, index=False)

    return MaterializationDefinition(
        materialization_type='CSV',
        materialization_fn=to_csv_fn,
        argument_def_dict={'path': types.PATH}
    )


def dataframe_parquet_materialization():
    def to_parquet_fn(df, context, arg_dict):
        check.inst_param(df, 'df', pd.DataFrame)
        check.inst_param(context, 'context', DagsterExecutionContext)
        check.dict_param(arg_dict, 'arg_dict')
        path = check.str_elem(arg_dict, 'path')

        df.to_parquet(path)

    return MaterializationDefinition(
        materialization_type='PARQUET',
        materialization_fn=to_parquet_fn,
        argument_def_dict={'path': types.PATH}
    )
