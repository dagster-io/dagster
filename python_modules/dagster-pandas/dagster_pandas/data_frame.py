import pandas as pd

from dagster import Dict, Field, Path, Selector, String, check, as_dagster_type

from dagster.core.types.config_schema import SelectorInputSchema, SelectorOutputSchema

from dagster.core.types.marshal import PickleMarshallingStrategy


def define_path_dict_field():
    return Field(Dict({'path': Field(Path)}))


def define_csv_dict_field():
    return Field(
        Dict({'path': Field(Path), 'sep': Field(String, is_optional=True, default_value=',')})
    )


class PandasDataFrameOutputSchema(SelectorOutputSchema):
    @property
    def schema_cls(self):
        return Selector(
            {
                'csv': define_csv_dict_field(),
                'parquet': define_path_dict_field(),
                'table': define_path_dict_field(),
            }
        )

    def materialize_selector_runtime_value(self, selector_key, selector_value, runtime_value):
        if selector_key == 'csv':
            path = selector_value['path']
            del selector_value['path']
            return runtime_value.to_csv(path, index=False, **selector_value)
        elif selector_key == 'parquet':
            return runtime_value.to_parquet(selector_value['path'])
        elif selector_key == 'table':
            return runtime_value.to_csv(selector_value['path'], sep='\t', index=False)
        else:
            check.failed('Unsupported file_type {file_type}'.format(file_type=selector_key))


class PandasDataFrameInputSchema(SelectorInputSchema):
    @property
    def schema_cls(self):
        return Selector(
            {
                'csv': define_csv_dict_field(),
                'parquet': define_path_dict_field(),
                'table': define_path_dict_field(),
            }
        )

    def construct_from_selector_value(self, selector_key, selector_value):
        if selector_key == 'csv':
            path = selector_value['path']
            del selector_value['path']
            return pd.read_csv(path, **selector_value)
        elif selector_key == 'parquet':
            return pd.read_parquet(selector_value['path'])
        elif selector_key == 'table':
            return pd.read_table(selector_value['path'])
        else:
            check.failed('Unsupported file_type {file_type}'.format(file_type=selector_key))


DataFrame = as_dagster_type(
    pd.DataFrame,
    name='PandasDataFrame',
    description='''Two-dimensional size-mutable, potentially heterogeneous
tabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/''',
    input_schema=PandasDataFrameInputSchema(),
    output_schema=PandasDataFrameOutputSchema(),
    marshalling_strategy=PickleMarshallingStrategy(),
)
