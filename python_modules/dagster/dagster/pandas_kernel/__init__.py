from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *  # pylint: disable=W0622,W0401

import pandas as pd

import dagster
from dagster import (check, types)


def parquet_dataframe_source(**read_parquet_kwargs):
    def callback(context, arg_dict):
        check.inst_param(context, 'context', dagster.ExecutionContext)
        check.str_param(arg_dict['path'], 'path')
        df = pd.read_parquet(arg_dict['path'], **read_parquet_kwargs)
        context.metric('rows', df.shape[0])
        return df

    return dagster.SourceDefinition(
        source_type='PARQUET',
        source_fn=callback,
        argument_def_dict={
            'path': dagster.ArgumentDefinition(dagster.types.Path),
        },
    )


def csv_dataframe_source(name=None, **read_csv_kwargs):
    def callback(context, arg_dict):
        check.inst_param(context, 'context', dagster.ExecutionContext)
        check.str_param(arg_dict['path'], 'path')
        df = pd.read_csv(arg_dict['path'], **read_csv_kwargs)
        context.metric('rows', df.shape[0])
        return df

    return dagster.SourceDefinition(
        source_type=check.opt_str_param(name, 'name', 'CSV'),
        source_fn=callback,
        argument_def_dict={
            'path': dagster.ArgumentDefinition(dagster.types.Path),
        },
    )


def table_dataframe_source(**read_table_kwargs):
    def callback(context, arg_dict):
        check.inst_param(context, 'context', dagster.ExecutionContext)
        path = check.str_elem(arg_dict, 'path')
        df = pd.read_table(path, **read_table_kwargs)
        context.metric('rows', df.shape[0])
        return df

    return dagster.SourceDefinition(
        source_type='TABLE',
        source_fn=callback,
        argument_def_dict={
            'path': dagster.ArgumentDefinition(dagster.types.Path),
        },
    )


def dataframe_csv_materialization():
    def to_csv_fn(context, arg_dict, df):
        check.inst_param(df, 'df', pd.DataFrame)
        check.inst_param(context, 'context', dagster.ExecutionContext)
        check.dict_param(arg_dict, 'arg_dict')
        path = check.str_elem(arg_dict, 'path')

        df.to_csv(path, index=False)

    return dagster.MaterializationDefinition(
        name='CSV',
        materialization_fn=to_csv_fn,
        argument_def_dict={'path': dagster.ArgumentDefinition(types.Path)},
    )


def dataframe_parquet_materialization():
    def to_parquet_fn(context, arg_dict, df):
        check.inst_param(df, 'df', pd.DataFrame)
        check.inst_param(context, 'context', dagster.ExecutionContext)
        check.dict_param(arg_dict, 'arg_dict')
        path = check.str_elem(arg_dict, 'path')

        df.to_parquet(path)

    return dagster.MaterializationDefinition(
        name='PARQUET',
        materialization_fn=to_parquet_fn,
        argument_def_dict={'path': dagster.ArgumentDefinition(types.Path)},
    )


def _create_dataframe_type():
    return dagster.types.PythonObjectType(
        name='PandasDataFrame',
        python_type=pd.DataFrame,
        description=
        '''Two-dimensional size-mutable, potentially heterogeneous tabular data structure with labeled axes (rows and columns).
        See http://pandas.pydata.org/
        ''',
        default_sources=[
            parquet_dataframe_source(),
            csv_dataframe_source(),
            table_dataframe_source(),
        ],
        default_materializations=[
            dataframe_csv_materialization(),
            dataframe_parquet_materialization(),
        ]
    )


DataFrame = _create_dataframe_type()
