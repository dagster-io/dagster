from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *  # pylint: disable=W0622,W0401

import pandas as pd

from dagster import (
    ArgumentDefinition,
    ExecutionContext,
    MaterializationDefinition,
    OutputDefinition,
    Result,
    SolidDefinition,
    check,
    types,
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


def _create_dataframe_type():
    return types.PythonObjectType(
        name='PandasDataFrame',
        python_type=pd.DataFrame,
        description=
        '''Two-dimensional size-mutable, potentially heterogeneous tabular data structure with labeled axes (rows and columns).
        See http://pandas.pydata.org/
        ''',
        default_materializations=[
            dataframe_csv_materialization(),
            dataframe_parquet_materialization(),
        ]
    )


DataFrame = _create_dataframe_type()


def load_csv_solid(name):
    check.str_param(name, 'name')

    def _t_fn(_context, _inputs, config_dict):
        yield Result(pd.read_csv(config_dict['path']))

    return SolidDefinition(
        name=name,
        inputs=[],
        outputs=[OutputDefinition(dagster_type=DataFrame)],
        transform_fn=_t_fn,
        config_def={
            'path': ArgumentDefinition(types.Path),
        }
    )
