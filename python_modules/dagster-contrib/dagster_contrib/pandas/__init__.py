from collections import namedtuple
import os
import pickle
import tempfile

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

from dagster.core.types.configurable import ConfigurableSelectorFromDict
from dagster.core.types.materializable import FileMarshalable, Materializeable

DataFrameMeta = namedtuple('DataFrameMeta', 'format path')


def define_path_dict_field():
    return Field(types.Dict({'path': Field(types.Path)}))


def define_csv_dict_field():
    return Field(
        types.Dict(
            {
                'path': Field(types.Path),
                'sep': Field(types.String, is_optional=True, default_value=','),
            }
        )
    )


class _PandasDataFrameMaterializationConfigSchema(ConfigurableSelectorFromDict, types.DagsterType):
    def __init__(self):
        super(_PandasDataFrameMaterializationConfigSchema, self).__init__(
            name='PandasDataFrameMaterializationConfigSchema',
            fields={
                'csv': define_csv_dict_field(),
                'parquet': define_path_dict_field(),
                'table': define_path_dict_field(),
            },
        )


PandasDataFrameMaterializationConfigSchema = _PandasDataFrameMaterializationConfigSchema()


class _DataFrameType(
    ConfigurableSelectorFromDict, types.PythonObjectType, Materializeable, FileMarshalable
):
    def __init__(self):
        super(_DataFrameType, self).__init__(
            name='PandasDataFrame',
            python_type=pd.DataFrame,
            description='''Two-dimensional size-mutable, potentially heterogeneous
    tabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/''',
            fields={
                'csv': define_csv_dict_field(),
                'parquet': define_path_dict_field(),
                'table': define_path_dict_field(),
            },
        )

    def marshal_value(self, value, to_file):
        with open(to_file, 'wb') as ff:
            pickle.dump(value, ff)

    def unmarshal_value(self, from_file):
        with open(from_file, 'rb') as ff:
            return pickle.load(ff)

    def define_materialization_config_schema(self):
        return PandasDataFrameMaterializationConfigSchema

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

    def create_serializable_type_value(self, value, output_dir):
        check.str_param(output_dir, 'output_dir')
        csv_path = os.path.join(output_dir, 'csv')
        value.to_csv(csv_path, index=False)
        df_meta = DataFrameMeta(format='csv', path='csv')
        import dagster.core.types.base

        return dagster.core.types.base.SerializedTypeValue(name=self.name, value=df_meta._asdict())

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
            return pd.read_parquet(file_options['path'])
        elif file_type == 'table':
            return pd.read_table(file_options['path'])
        else:
            check.failed('Unsupported file_type {file_type}'.format(file_type=file_type))


DataFrame = _DataFrameType()
