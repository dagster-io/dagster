import itertools
import re
from typing import TYPE_CHECKING, Callable, List, Type, Union

import dagster.check as check
import pandas as pd
import pandera as pa
from dagster import (
    DagsterType,
    EventMetadataEntry,
    TypeCheck,
    TableColumn,
    TableColumnConstraints,
    TableConstraints,
    TableRecord,
    TableSchema,
    TypeCheckContext,
)
from dagster.core.utils import check_dagster_package_version

from .version import __version__

# NOTE: Pandera supports multiple dataframe libraries. Most of the alternatives
# to pandas implement a pandas-like API wrapper around an underlying library
# that can handle big data (a weakness of pandas). Typically this means the
# data is only partly loaded into memory, or is distributed across multiple
# nodes. Because Dagster types perform runtime validation within a single
# Python process, it's not clear at present how to interface the more complex
# validation computations on distributed dataframes with Dagster Types.

# Therefore, for the time being dagster-pandera only supports pandas dataframes.
# However, some commented-out scaffolding has been left in place for support of
# alternatives in the future. These sections are marked with "TODO: pending
# alternative dataframe support".

if TYPE_CHECKING:
    ValidatableDataFrame = pd.DataFrame

check_dagster_package_version("dagster-pandera", __version__)

# ########################
# ##### VALID DATAFRAME CLASSES
# ########################

# This layer of indirection is used because we may support alternative dataframe classes in the
# future.
VALID_DATAFRAME_CLASSES = (pd.DataFrame,)


# ########################
# ##### PANDERA SCHEMA TO DAGSTER TYPE
# ########################


def pandera_schema_to_dagster_type(
    schema: Union[pa.DataFrameSchema, Type[pa.SchemaModel]],
) -> DagsterType:
    """
    Convert a Pandera dataframe schema to a `DagsterType`.

    The generated Dagster type will be given an automatically generated `name`. The schema's `title`
    property, `name` property, or class name (in that order) will be used. If neither `title` or
    `name` is defined, a name of the form `DagsterPanderaDataframe<n>` is generated.

    Additional metadata is also extracted from the Pandera schema and attached to the returned
    `DagsterType` in an `EventMetadataEntry` object. The extracted metadata includes:

    - Descriptions on the schema and constituent columns and checks.
    - Data types for each column.
    - String representations of all column-wise checks.
    - String representations of all row-wise (i.e. "wide") checks.

    The returned `DagsterType` type will call the Pandera schema's `validate()` method in its type
    check function. Validation is done in `lazy` mode, i.e. pandera will attempt to validate all
    values in the dataframe, rather than stopping on the first error.

    If validation fails, the returned `TypeCheck` object will contain two pieces of metadata:

    - `num_failures` total number of validation errors.
    - `failure_sample` a table containing up to the first 10 validation errors.

    Args:
        schema (Union[pa.DataFrameSchema, Type[pa.SchemaModel]]):

    Returns:
        DagsterType: Dagster Type constructed from the Pandera schema.

    """
    if not (
        isinstance(schema, pa.DataFrameSchema)
        or (isinstance(schema, type) and issubclass(schema, pa.SchemaModel))
    ):
        raise TypeError(
            "schema must be a pandera `DataFrameSchema` or a subclass of a pandera `SchemaModel`"
        )

    name = _extract_name_from_pandera_schema(schema)
    norm_schema = (
        schema.to_schema()
        if isinstance(schema, type) and issubclass(schema, pa.SchemaModel)
        else schema
    )
    tschema = _pandera_schema_to_table_schema(norm_schema)
    type_check_fn = _pandera_schema_to_type_check_fn(norm_schema, tschema)

    return DagsterType(
        type_check_fn=type_check_fn,
        name=name,
        description=norm_schema.description,
        metadata_entries=[
            EventMetadataEntry.table_schema(tschema, label="schema"),
        ],
    )


# call next() on this to generate next unique Dagster Type name for anonymous schemas
_anonymous_schema_name_generator = (f"DagsterPanderaDataframe{i}" for i in itertools.count(start=1))


def _extract_name_from_pandera_schema(
    schema: Union[pa.DataFrameSchema, Type[pa.SchemaModel]],
) -> str:
    if isinstance(schema, type) and issubclass(schema, pa.SchemaModel):
        return (
            getattr(schema.Config, "title", None)
            or getattr(schema.Config, "name", None)
            or schema.__name__
        )
    elif isinstance(schema, pa.DataFrameSchema):
        return schema.title or schema.name or next(_anonymous_schema_name_generator)


def _pandera_schema_to_type_check_fn(
    schema: pa.DataFrameSchema,
    table_schema: TableSchema,
) -> Callable[[TypeCheckContext, object], TypeCheck]:
    def type_check_fn(_context, value: object) -> TypeCheck:
        if isinstance(value, VALID_DATAFRAME_CLASSES):
            try:
                # `lazy` instructs pandera to capture every (not just the first) validation error
                schema.validate(value, lazy=True)
            except pa.errors.SchemaErrors as e:
                return _pandera_errors_to_type_check(e, table_schema)
            except Exception as e:
                return TypeCheck(
                    success=False,
                    description=f"Unexpected error during validation: {e}",
                )
        else:
            return TypeCheck(
                success=False,
                description=f"Must be one of {VALID_DATAFRAME_CLASSES}, not {type(value).__name__}.",
            )

        return TypeCheck(success=True)

    return type_check_fn


def _pandera_errors_to_type_check(
    error: pa.errors.SchemaErrors, table_schema: TableSchema
) -> TypeCheck:
    return TypeCheck(
        success=False,
        description=str(error),
        metadata_entries=[
            EventMetadataEntry.int(len(error.failure_cases), "Num failures"),
            EventMetadataEntry.table(
                label="Failure cases (first 10)",
                records=[
                    TableRecord(**row._asdict())
                    for row in itertools.islice(error.failure_cases.itertuples(), 10)
                ],
            ),
            EventMetadataEntry.table_schema(table_schema, label="schema"),
        ],
    )


def _pandera_schema_to_table_schema(schema: pa.DataFrameSchema) -> TableSchema:
    df_constraints = _pandera_schema_wide_checks_to_table_constraints(schema.checks)
    columns = [_pandera_column_to_table_column(col) for k, col in schema.columns.items()]
    return TableSchema(columns=columns, constraints=df_constraints)


def _pandera_schema_wide_checks_to_table_constraints(
    checks: List[Union[pa.Check, pa.Hypothesis]]
) -> TableConstraints:
    return TableConstraints(other=[_pandera_check_to_table_constraint(check) for check in checks])


def _pandera_check_to_table_constraint(pa_check: Union[pa.Check, pa.Hypothesis]) -> str:
    return pa_check.description or pa_check.error


def _pandera_column_to_table_column(pa_column: pa.Column) -> TableColumn:
    constraints = TableColumnConstraints(
        nullable=pa_column.nullable,
        unique=pa_column.unique,
        other=[_pandera_check_to_column_constraint(pa_check) for pa_check in pa_column.checks],
    )
    name = check.not_none(pa_column.name, "name")
    return TableColumn(
        name=name,
        type=str(pa_column.dtype),
        description=pa_column.description,
        constraints=constraints,
    )


CHECK_OPERATORS = {
    "equal_to": "==",
    "not_equal_to": "!=",
    "greater_than_or_equal_to": "!=",
    "less_than": "<",
    "less_than_or_equal_to": "<=",
    "greater_than": ">",
    "greater_than_or_equal_to": ">=",
    "in": "in",
    "not_in": "not in",
}


def _extract_operand(error_str: str) -> str:
    match = re.search(r"(?<=\().+(?=\))", error_str)
    return match.group(0) if match else ""


def _pandera_check_to_column_constraint(pa_check: pa.Check) -> str:
    if pa_check.description:
        return pa_check.description
    elif pa_check.name in CHECK_OPERATORS:
        return f"{CHECK_OPERATORS[pa_check.name]} {_extract_operand(pa_check.error)}"
    else:
        return pa_check.error


__all__ = [
    "pandera_schema_to_dagster_type",
]
