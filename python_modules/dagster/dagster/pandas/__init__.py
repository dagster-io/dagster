from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *  # pylint: disable=W0622,W0401

import pandas as pd

from dagster import (
    ConfigDefinition,
    Field,
    ExecutionContext,
    InputDefinition,
    OutputDefinition,
    Result,
    SolidDefinition,
    check,
    types,
)


def _create_dataframe_type():
    return types.PythonObjectType(
        name='PandasDataFrame',
        python_type=pd.DataFrame,
        description='''Two-dimensional size-mutable, potentially heterogeneous
tabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/''',
    )


DataFrame = _create_dataframe_type()


def load_csv_solid(name):
    check.str_param(name, 'name')

    def _t_fn(info, _inputs):
        yield Result(pd.read_csv(info.config['path']))

    return SolidDefinition(
        name=name,
        inputs=[],
        outputs=[OutputDefinition(DataFrame)],
        transform_fn=_t_fn,
        config_def=ConfigDefinition.config_dict({
            'path': Field(types.Path),
        }),
    )


def to_csv_solid(name):
    def _t_fn(info, inputs):
        inputs['df'].to_csv(info.config['path'], index=False)

    return SolidDefinition(
        name=name,
        inputs=[InputDefinition('df', DataFrame)],
        outputs=[],
        config_def=ConfigDefinition.config_dict({
            'path': Field(types.Path)
        }),
        transform_fn=_t_fn,
    )


def to_parquet_solid(name):
    def _t_fn(info, inputs):
        inputs['df'].to_parquet(info.config['path'])

    return SolidDefinition(
        name=name,
        inputs=[InputDefinition('df', DataFrame)],
        outputs=[],
        config_def=ConfigDefinition.config_dict({
            'path': Field(types.Path)
        }),
        transform_fn=_t_fn,
    )
