import pandas as pd

from dagster import (
    DagsterInvariantViolationError,
    Dict,
    EventMetadataEntry,
    Field,
    Materialization,
    Path,
    String,
    TypeCheck,
    as_dagster_type,
    check,
)
from dagster.core.types import NamedSelector, input_selector_schema, output_selector_schema


def define_path_dict_field():
    return Field(Dict({'path': Field(Path)}))


def define_csv_dict_field():
    return Field(
        Dict({'path': Field(Path), 'sep': Field(String, is_optional=True, default_value=',')})
    )


def dict_without_keys(ddict, *keys):
    return {key: value for key, value in ddict.items() if key not in set(keys)}


@output_selector_schema(
    NamedSelector(
        'DataFrameOutputSchema',
        {
            'csv': define_csv_dict_field(),
            'parquet': define_path_dict_field(),
            'table': define_path_dict_field(),
        },
    )
)
def dataframe_output_schema(_context, file_type, file_options, pandas_df):
    check.str_param(file_type, 'file_type')
    check.dict_param(file_options, 'file_options')
    check.inst_param(pandas_df, 'pandas_df', DataFrame)

    if file_type == 'csv':
        path = file_options['path']
        pandas_df.to_csv(path, index=False, **dict_without_keys(file_options, 'path'))
    elif file_type == 'parquet':
        pandas_df.to_parquet(file_options['path'])
    elif file_type == 'table':
        pandas_df.to_csv(file_options['path'], sep='\t', index=False)
    else:
        check.failed('Unsupported file_type {file_type}'.format(file_type=file_type))

    return Materialization.file(file_options['path'])


@input_selector_schema(
    NamedSelector(
        'DataFrameInputSchema',
        {
            'csv': define_csv_dict_field(),
            'parquet': define_path_dict_field(),
            'table': define_path_dict_field(),
        },
    )
)
def dataframe_input_schema(_context, file_type, file_options):
    check.str_param(file_type, 'file_type')
    check.dict_param(file_options, 'file_options')

    if file_type == 'csv':
        path = file_options['path']
        return pd.read_csv(path, **dict_without_keys(file_options, 'path'))
    elif file_type == 'parquet':
        return pd.read_parquet(file_options['path'])
    elif file_type == 'table':
        return pd.read_csv(file_options['path'], sep='\t')
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
    input_hydration_config=dataframe_input_schema,
    output_materialization_config=dataframe_output_schema,
    typecheck_metadata_fn=lambda value: TypeCheck(
        metadata_entries=[
            EventMetadataEntry.text(str(len(value)), 'row_count', 'Number of rows in DataFrame'),
            # string cast columns since they may be things like datetime
            EventMetadataEntry.json({'columns': list(map(str, value.columns))}, 'metadata'),
        ]
    ),
)
