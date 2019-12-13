import pandas as pd
from dagster_pandas.constraints import (
    ColumnExistsConstraint,
    ColumnTypeConstraint,
    ConstraintViolationException,
)
from dagster_pandas.validation import PandasColumn, validate_collection_schema

from dagster import (
    DagsterInvariantViolationError,
    EventMetadataEntry,
    Field,
    Materialization,
    Path,
    String,
    TypeCheck,
    as_dagster_type,
    check,
    dagster_type,
)
from dagster.core.types.config.field_utils import NamedSelector
from dagster.core.types.runtime.config_schema import input_selector_schema, output_selector_schema


def dict_without_keys(ddict, *keys):
    return {key: value for key, value in ddict.items() if key not in set(keys)}


@output_selector_schema(
    NamedSelector(
        'DataFrameOutputSchema',
        {
            'csv': {'path': Path, 'sep': Field(String, is_optional=True, default_value=','),},
            'parquet': {'path': Path},
            'table': {'path': Path},
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
            'csv': {'path': Path, 'sep': Field(String, is_optional=True, default_value=','),},
            'parquet': {'path': Path},
            'table': {'path': Path},
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


def df_type_check(value):
    if not isinstance(value, pd.DataFrame):
        return TypeCheck(success=False)
    return TypeCheck(
        success=True,
        metadata_entries=[
            EventMetadataEntry.text(str(len(value)), 'row_count', 'Number of rows in DataFrame'),
            # string cast columns since they may be things like datetime
            EventMetadataEntry.json({'columns': list(map(str, value.columns))}, 'metadata'),
        ],
    )


DataFrame = as_dagster_type(
    pd.DataFrame,
    name='PandasDataFrame',
    description='''Two-dimensional size-mutable, potentially heterogeneous
    tabular data structure with labeled axes (rows and columns).
    See http://pandas.pydata.org/''',
    input_hydration_config=dataframe_input_schema,
    output_materialization_config=dataframe_output_schema,
    type_check=df_type_check,
)


def create_dagster_pandas_dataframe_type(name=None, type_check=None, columns=None):
    def _dagster_type_check(value):
        if columns is not None:
            try:
                validate_collection_schema(columns, value)
            except ConstraintViolationException as e:
                return TypeCheck(success=False, description=str(e))
        return type_check(value)

    @dagster_type(  # pylint: disable=W0223
        name=name, type_check=_dagster_type_check,
    )
    class _DataFrameDagsterType(DataFrame):
        pass

    # Did this instead of as_dagster_type because multiple dataframe types can be created
    return _DataFrameDagsterType


def create_typed_dataframe(dataframe_name, column_type_info, type_check=None):
    column_type_info = check.dict_param(column_type_info, 'column_type_info', str, str)
    return create_dagster_pandas_dataframe_type(
        name=check.str_param(dataframe_name, 'dataframe_name'),
        type_check=check.opt_callable_param(type_check, 'type_check'),
        columns=[
            PandasColumn(
                name=column_name,
                constraints=[ColumnExistsConstraint(), ColumnTypeConstraint(column_pandas_dtype)],
            )
            for column_name, column_pandas_dtype in column_type_info.items()
        ],
    )


def create_named_dataframe(dataframe_name, column_names, type_check=None):
    return create_dagster_pandas_dataframe_type(
        name=check.str_param(dataframe_name, 'dataframe_name'),
        type_check=check.opt_callable_param(type_check, 'type_check'),
        columns=[
            PandasColumn(name=column_name, constraints=[ColumnExistsConstraint()])
            for column_name in check.list_param(column_names, 'column_names', of_type=str)
        ],
    )
