import pandas as pd

from dagster import Dict, Field, Path, Selector, String, check, make_dagster_type

from dagster.core.types.config_schema import InputSchema, OutputSchema

from dagster.core.types.marshal import PickleMarshallingStrategy


def define_path_dict_field():
    return Field(Dict({'path': Field(Path)}))


def define_csv_dict_field():
    return Field(
        Dict({'path': Field(Path), 'sep': Field(String, is_optional=True, default_value=',')})
    )


class PandasDataFrameOutputSchema(OutputSchema):
    @property
    def schema_cls(self):
        return Selector(
            {
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


class PandasDataFrameInputSchema(InputSchema):
    @property
    def schema_cls(self):
        return Selector(
            {
                'csv': define_csv_dict_field(),
                'parquet': define_path_dict_field(),
                'table': define_path_dict_field(),
            }
        )

    def construct_from_config_value(self, value):
        file_type, file_options = list(value.items())[0]
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


DataFrame = make_dagster_type(
    pd.DataFrame,
    name='PandasDataFrame',
    description='''Two-dimensional size-mutable, potentially heterogeneous
tabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/''',
    input_schema=PandasDataFrameInputSchema(),
    output_schema=PandasDataFrameOutputSchema(),
    marshalling_strategy=PickleMarshallingStrategy(),
)
