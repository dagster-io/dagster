from collections import namedtuple
import os
import pickle
import tempfile

import six

import pandas as pd

from dagster import (
    Field,
    ExecutionContext,
    InputDefinition,
    OutputDefinition,
    Result,
    SolidDefinition,
    check,
    types,
)

from dagster.core.configurable import ConfigurableSelectorFromDict

DataFrameMeta = namedtuple('DataFrameMeta', 'format path')


class _DataFrameType(ConfigurableSelectorFromDict, types.PythonObjectType):
    def __init__(self):
        super(_DataFrameType, self).__init__(
            name='PandasDataFrame',
            python_type=pd.DataFrame,
            description='''Two-dimensional size-mutable, potentially heterogeneous
    tabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/''',
            fields={
                'csv':
                types.Field(
                    types.Dict(
                        {
                            'path': types.Field(types.Path),
                            'sep': types.Field(types.String, is_optional=True, default_value=','),
                        },
                    ),
                ),
                'parquet':
                types.Field(types.Dict({
                    'path': types.Field(types.Path),
                })),
                'table':
                types.Field(types.Dict({
                    'path': types.Field(types.Path),
                })),
            },
        )

    def create_serializable_type_value(self, value, output_dir):
        check.str_param(output_dir, 'output_dir')
        csv_path = os.path.join(output_dir, 'csv')
        value.to_csv(csv_path, index=False)
        df_meta = DataFrameMeta(format='csv', path='csv')
        return types.SerializedTypeValue(name=self.name, value=df_meta._asdict())

    def deserialize_from_type_value(self, type_value, output_dir):
        check.str_param(output_dir, 'output_dir')

        df_meta_dict = type_value.value
        check.inst(df_meta_dict, dict)
        df_meta = DataFrameMeta(**df_meta_dict)

        if df_meta.format == 'csv':
            csv_path = os.path.join(output_dir, df_meta.path)
            return pd.read_csv(csv_path)
        else:
            raise Exception('unsupported')

    def construct_from_config_value(self, config_value):
        file_type, file_options = list(config_value.items())[0]
        if file_type == 'csv':
            path = file_options['path']
            del file_options['path']
            return pd.read_csv(path, **file_options)
        elif file_type == 'parquet':
            path = file_options['path']
            return pd.read_parquet(file_options['path'])
        elif file_type == 'table':
            return pd.read_table(file_options['path'])
        else:
            check.failed('Unsupported file_type {file_type}'.format(file_type=file_type))


DataFrame = _DataFrameType()


def path_dict_field():
    return Field(types.Dict({'path': Field(types.Path)}))


def load_csv_solid(name):
    check.str_param(name, 'name')

    def _t_fn(info, _inputs):
        yield Result(pd.read_csv(info.config['path']))

    return SolidDefinition(
        name=name,
        inputs=[],
        outputs=[OutputDefinition(DataFrame)],
        transform_fn=_t_fn,
        config_field=path_dict_field(),
    )


def to_csv_solid(name):
    def _t_fn(info, inputs):
        inputs['df'].to_csv(info.config['path'], index=False)

    return SolidDefinition(
        name=name,
        inputs=[InputDefinition('df', DataFrame)],
        outputs=[],
        config_field=path_dict_field(),
        transform_fn=_t_fn,
    )


def to_parquet_solid(name):
    def _t_fn(info, inputs):
        inputs['df'].to_parquet(info.config['path'])

    return SolidDefinition(
        name=name,
        inputs=[InputDefinition('df', DataFrame)],
        outputs=[],
        config_field=path_dict_field(),
        transform_fn=_t_fn,
    )
