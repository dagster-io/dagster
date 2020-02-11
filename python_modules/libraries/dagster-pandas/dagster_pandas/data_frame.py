import pandas as pd
from dagster_pandas.constraints import (
    ColumnExistsConstraint,
    ColumnTypeConstraint,
    ConstraintViolationException,
)
from dagster_pandas.validation import PandasColumn, validate_constraints

from dagster import (
    DagsterInvariantViolationError,
    DagsterType,
    EventMetadataEntry,
    Field,
    Materialization,
    Path,
    String,
    TypeCheck,
    check,
)
from dagster.config.field_utils import Selector
from dagster.core.types.config_schema import input_selector_schema, output_selector_schema

CONSTRAINT_BLACKLIST = {ColumnExistsConstraint, ColumnTypeConstraint}


def dict_without_keys(ddict, *keys):
    return {key: value for key, value in ddict.items() if key not in set(keys)}


@output_selector_schema(
    Selector(
        {
            'csv': {'path': Path, 'sep': Field(String, is_required=False, default_value=','),},
            'parquet': {'path': Path},
            'table': {'path': Path},
        },
    )
)
def dataframe_output_schema(_context, file_type, file_options, pandas_df):
    check.str_param(file_type, 'file_type')
    check.dict_param(file_options, 'file_options')
    check.inst_param(pandas_df, 'pandas_df', pd.DataFrame)

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
    Selector(
        {
            'csv': {'path': Path, 'sep': Field(String, is_required=False, default_value=','),},
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


def df_type_check(_, value):
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


DataFrame = DagsterType(
    name='PandasDataFrame',
    description='''Two-dimensional size-mutable, potentially heterogeneous
    tabular data structure with labeled axes (rows and columns).
    See http://pandas.pydata.org/''',
    input_hydration_config=dataframe_input_schema,
    output_materialization_config=dataframe_output_schema,
    type_check_fn=df_type_check,
)


def _construct_constraint_list(constraints):
    def add_bullet(constraint_list, constraint_description):
        return constraint_list + "+ {constraint_description}\n".format(
            constraint_description=constraint_description
        )

    constraint_list = ""
    for constraint in constraints:
        if constraint.__class__ not in CONSTRAINT_BLACKLIST:
            constraint_list = add_bullet(constraint_list, constraint.markdown_description)
    return constraint_list


def _build_column_header(column_name, constraints):
    expected_column_types = None
    column_type_constraint = [
        constraint for constraint in constraints if isinstance(constraint, ColumnTypeConstraint)
    ]
    if column_type_constraint:
        expected_types = tuple(column_type_constraint[0].expected_pandas_dtypes)
        if expected_types:
            expected_column_types = (
                expected_types[0] if len(expected_types) == 1 else tuple(expected_types)
            )

    column_header = '**{column_name}**'.format(column_name=column_name)
    if expected_column_types:
        column_header += ": `{expected_dtypes}`".format(expected_dtypes=expected_column_types)
    return column_header


def create_dagster_pandas_dataframe_description(description, columns):
    title = "\n".join([description, '### Columns', ''])
    buildme = title
    for column in columns:
        buildme += "{}\n{}\n".format(
            _build_column_header(column.name, column.constraints),
            _construct_constraint_list(column.constraints),
        )
    return buildme


def create_dagster_pandas_dataframe_type(
    name=None, description=None, columns=None, event_metadata_fn=None, dataframe_constraints=None
):
    event_metadata_fn = check.opt_callable_param(event_metadata_fn, 'event_metadata_fn')
    description = create_dagster_pandas_dataframe_description(
        check.opt_str_param(description, 'description', default=''),
        check.opt_list_param(columns, 'columns', of_type=PandasColumn),
    )

    def _dagster_type_check(_, value):
        if not isinstance(value, pd.DataFrame):
            return TypeCheck(
                success=False,
                description='Must be a pandas.DataFrame. Got value of type. {type_name}'.format(
                    type_name=type(value).__name__
                ),
            )

        try:
            validate_constraints(
                value, pandas_columns=columns, dataframe_constraints=dataframe_constraints
            )
        except ConstraintViolationException as e:
            return TypeCheck(success=False, description=str(e))

        return TypeCheck(
            success=True,
            metadata_entries=_execute_summary_stats(name, value, event_metadata_fn)
            if event_metadata_fn
            else None,
        )

    # add input_hydration_confign and output_materialization_config
    # https://github.com/dagster-io/dagster/issues/2027
    return DagsterType(name=name, type_check_fn=_dagster_type_check, description=description)


def _execute_summary_stats(type_name, value, event_metadata_fn):
    if not event_metadata_fn:
        return []

    metadata_entries = event_metadata_fn(value)

    if not (
        isinstance(metadata_entries, list)
        and all(isinstance(item, EventMetadataEntry) for item in metadata_entries)
    ):
        raise DagsterInvariantViolationError(
            (
                'The return value of the user-defined summary_statistics function '
                'for pandas data frame type {type_name} returned {value}. '
                'This function must return List[EventMetadataEntry]'
            ).format(type_name=type_name, value=repr(metadata_entries))
        )

    return metadata_entries
