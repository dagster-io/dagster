import pandas as pd

from dagster import (
    as_dagster_type,
    check,
    DagsterInvariantViolationError,
    Dict,
    Field,
    input_selector_schema,
    output_selector_schema,
    Path,
    Selector,
    String,
)


def define_path_dict_field():
    return Field(Dict({'path': Field(Path)}))


def define_csv_dict_field():
    return Field(
        Dict({'path': Field(Path), 'sep': Field(String, is_optional=True, default_value=',')})
    )


@output_selector_schema(
    Selector(
        {
            'csv': define_csv_dict_field(),
            'parquet': define_path_dict_field(),
            'table': define_path_dict_field(),
        }
    )
)
def dataframe_output_schema(file_type, file_options, pandas_df):
    check.str_param(file_type, 'file_type')
    check.dict_param(file_options, 'file_options')
    check.inst_param(pandas_df, 'pandas_df', DataFrame)

    if file_type == 'csv':
        path = file_options['path']
        del file_options['path']
        return pandas_df.to_csv(path, index=False, **file_options)
    elif file_type == 'parquet':
        return pandas_df.to_parquet(file_options['path'])
    elif file_type == 'table':
        return pandas_df.to_csv(file_options['path'], sep='\t', index=False)
    else:
        check.failed('Unsupported file_type {file_type}'.format(file_type=file_type))


@input_selector_schema(
    Selector(
        {
            'csv': define_csv_dict_field(),
            'parquet': define_path_dict_field(),
            'table': define_path_dict_field(),
        }
    )
)
def dataframe_input_schema(file_type, file_options):
    check.str_param(file_type, 'file_type')
    check.dict_param(file_options, 'file_options')

    if file_type == 'csv':
        path = file_options['path']
        del file_options['path']
        return pd.read_csv(path, **file_options)
    elif file_type == 'parquet':
        return pd.read_parquet(file_options['path'])
    elif file_type == 'table':
        return pd.read_table(file_options['path'])
    else:
        raise DagsterInvariantViolationError(
            'Unsupported file_type {file_type}'.format(file_type=file_type)
        )


DataFrame = as_dagster_type(
    pd.DataFrame,
    name='PandasDataFrame',
    description='''Two-dimensional size-mutable, potentially heterogeneous
    tabular data structure with labeled axes (rows and columns).
    See http://pandas.pydata.org/''',
    input_schema=dataframe_input_schema,
    output_schema=dataframe_output_schema,
)
