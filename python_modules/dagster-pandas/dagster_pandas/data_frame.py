from collections import namedtuple
import os
import pickle

import pandas as pd

from dagster import (
    check,
    Dict,
    ExecutionContext,
    Field,
    InputDefinition,
    OutputDefinition,
    Path,
    Result,
    SolidDefinition,
    String,
    types,
)

from dagster.core.types.field import ConfigSelector

from dagster.core.types.materializable import FileMarshalable, Materializeable

DataFrameMeta = namedtuple('DataFrameMeta', 'format path')


def define_path_dict_field():
    return Field(Dict({'path': Field(Path)}))


def define_csv_dict_field():
    return Field(
        Dict({'path': Field(Path), 'sep': Field(String, is_optional=True, default_value=',')})
    )


class PandasDataFrameInputSchema(ConfigSelector):
    def __init__(self):
        super(PandasDataFrameInputSchema, self).__init__(
            fields={
                'csv': define_csv_dict_field(),
                'parquet': define_path_dict_field(),
                'table': define_path_dict_field(),
            }
        )

    def construct_from_config_value(self, config_value):
        file_type, file_options = list(config_value.items())[0]
        if file_type == 'csv':
            path = file_options['path']
            del file_options['path']
            return pd.read_csv(path, **file_options)
        elif file_type == 'parquet':
            return pd.read_parquet(file_options['path'])
        elif file_type == 'table':
            return pd.read_table(file_options['path'])
        else:
            check.failed('Unsupported file_type {file_type}'.format(file_type=file_type))


class PandasDataFrameOutputConfigSchema(ConfigSelector):
    def __init__(self):
        super(PandasDataFrameOutputConfigSchema, self).__init__(
            fields={
                'csv': define_csv_dict_field(),
                'parquet': define_path_dict_field(),
                'table': define_path_dict_field(),
            }
        )

    def materialize_runtime_value(self, config_spec, runtime_value):
        file_type, file_options = list(config_spec.items())[0]
        if file_type == 'csv':
            path = file_options['path']
            del file_options['path']
            return runtime_value.to_csv(path, index=False, **file_options)
        elif file_type == 'parquet':
            return runtime_value.to_parquet(file_options['path'])
        elif file_type == 'table':
            return runtime_value.to_csv(file_options['path'], sep='\t', index=False)
        else:
            check.failed('Unsupported file_type {file_type}'.format(file_type=file_type))
        check.failed('must implement')


class DataFrame(FileMarshalable, types.PythonObjectType):
    def __init__(self):
        super(DataFrame, self).__init__(
            name='PandasDataFrame',
            python_type=pd.DataFrame,
            description='''Two-dimensional size-mutable, potentially heterogeneous
    tabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/''',
            input_schema_cls=PandasDataFrameInputSchema,
            output_schema_cls=PandasDataFrameOutputConfigSchema,
        )

    def marshal_value(self, value, to_file):
        with open(to_file, 'wb') as ff:
            pickle.dump(value, ff)

    def unmarshal_value(self, from_file):
        with open(from_file, 'rb') as ff:
            return pickle.load(ff)

    def define_materialization_config_schema(self):
        return PandasDataFrameOutputConfigSchema
