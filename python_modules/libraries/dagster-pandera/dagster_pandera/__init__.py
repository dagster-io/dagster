import itertools
import re
from collections.abc import Sequence
from typing import TYPE_CHECKING, Callable, Type, Union  # noqa: F401, UP035

import pandas as pd

# NOTE: Pandera supports multiple dataframe libraries. Most of the alternatives
# to pandas implement a pandas-like API wrapper around an underlying library
# that can handle big data (a weakness of pandas). Typically this means the
# data is only partly loaded into memory, or is distributed across multiple
# nodes. Because Dagster types perform runtime validation within a single
# Python process, it's not clear at present how to interface the more complex
# validation computations on distributed dataframes with Dagster Types.
# Therefore, for the time being dagster-pandera only supports pandas dataframes.
# However, some commented-out scaffolding has been left in place for support of
# alternatives in the future. These sections are marked with:
# "TODO: pending alternative dataframe support"
import pandera as pa

# Currently assume pandas support (prefer pandera.pandas, fallback to main pandera for old versions)
# TODO: pending alternative dataframe support
import pandera.pandas as pa_pd

# Try polars support
try:
    import pandera.polars as pa_pl
    import polars as pl
except ImportError:
    pa_pl = None
    pl = None

if TYPE_CHECKING:
    import pandera.pandas

    try:
        import pandera.polars  # noqa: TC004
    except ImportError:
        pass

from typing import TypeAlias

import dagster._check as check
import pandera.errors as pa_errors
from dagster import (
    DagsterType,
    TableColumn,
    TableColumnConstraints,
    TableConstraints,
    TableSchema,
    TypeCheck,
    TypeCheckContext,
)
from dagster._annotations import beta
from dagster._core.definitions.metadata import MetadataValue
from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_pandera.version import __version__

# Set up valid classes based on available imports
if pa_pd and pa_pl and pl:
    # TODO: pending alternative dataframe support
    VALID_DATAFRAME_CLASSES = (pd.DataFrame, pl.DataFrame)
    VALID_SCHEMA_CLASSES = (pa_pd.DataFrameSchema, pa_pl.DataFrameSchema)
    VALID_SCHEMA_MODEL_CLASSES = (pa_pd.DataFrameModel, pa_pl.DataFrameModel)
    VALID_COLUMN_CLASSES = (pa_pd.Column, pa_pl.Column)
elif pa_pd and pd:
    VALID_DATAFRAME_CLASSES = (pd.DataFrame,)
    VALID_SCHEMA_CLASSES = (pa_pd.DataFrameSchema,)
    VALID_SCHEMA_MODEL_CLASSES = (pa_pd.DataFrameModel,)
    VALID_COLUMN_CLASSES = (pa_pd.Column,)
else:
    # TODO: pending alternative dataframe support
    raise ImportError(
        "Unable to import pandera pandas functionality. This could be due to:\n"
        "1. Using Pandera < 0.24.0.'\n"
        "2. Missing pandas dependency.\n"
        "Please install pandera >= 0.24.0 with pandas to use dagster-pandera."
    )

DagsterPanderaSchema: TypeAlias = Union[pa_pd.DataFrameSchema, "pandera.polars.DataFrameSchema"]
DagsterPanderaSchemaModel: TypeAlias = type[
    Union[pa_pd.DataFrameModel, "pandera.polars.DataFrameModel"]
]
DagsterPanderaColumn: TypeAlias = Union[pa_pd.Column, "pandera.polars.Column"]

DagsterLibraryRegistry.register("dagster-pandera", __version__)

# ########################
# ##### PANDERA SCHEMA TO DAGSTER TYPE
# ########################


@beta
def pandera_schema_to_dagster_type(
    schema: Union[DagsterPanderaSchema, DagsterPanderaSchemaModel],
) -> DagsterType:
    """Convert a Pandera dataframe schema to a `DagsterType`.

    The generated Dagster type will be given an automatically generated `name`. The schema's `title`
    property, `name` property, or class name (in that order) will be used. If neither `title` or
    `name` is defined, a name of the form `DagsterPanderaDataframe<n>` is generated.

    Additional metadata is also extracted from the Pandera schema and attached to the returned
    `DagsterType` as a metadata dictionary. The extracted metadata includes:

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
        schema (Union[pa.DataFrameSchema, Type[pa.DataFrameModel]])

    Returns:
        DagsterType: Dagster Type constructed from the Pandera schema.

    """
    if not (
        isinstance(schema, VALID_SCHEMA_CLASSES)
        or (isinstance(schema, type) and issubclass(schema, VALID_SCHEMA_MODEL_CLASSES))
    ):
        raise TypeError(
            "schema must be a pandera `DataFrameSchema` or a subclass of a pandera `DataFrameModel`"
        )

    name = _extract_name_from_pandera_schema(schema)
    norm_schema = (
        schema.to_schema()
        if isinstance(schema, type) and issubclass(schema, VALID_SCHEMA_MODEL_CLASSES)
        else schema
    )
    tschema = _pandera_schema_to_table_schema(norm_schema)
    type_check_fn = _pandera_schema_to_type_check_fn(norm_schema, tschema)

    return DagsterType(
        type_check_fn=type_check_fn,
        name=name,
        description=norm_schema.description,
        metadata={
            "schema": MetadataValue.table_schema(tschema),
        },
        typing_type=pd.DataFrame,  # TODO: pending alternative dataframe support
    )


# call next() on this to generate next unique Dagster Type name for anonymous schemas
_anonymous_schema_name_generator = (f"DagsterPanderaDataframe{i}" for i in itertools.count(start=1))


def _extract_name_from_pandera_schema(
    schema: Union[DagsterPanderaSchema, DagsterPanderaSchemaModel],
) -> str:
    if isinstance(schema, type) and issubclass(schema, VALID_SCHEMA_MODEL_CLASSES):
        return str(
            getattr(schema.Config, "title", None)
            or getattr(schema.Config, "name", None)
            or schema.__name__
        )
    elif isinstance(schema, VALID_SCHEMA_CLASSES):
        return str(schema.title or schema.name or next(_anonymous_schema_name_generator))
    else:
        return next(_anonymous_schema_name_generator)


def _pandera_schema_to_type_check_fn(
    schema: DagsterPanderaSchema,
    table_schema: TableSchema,
) -> Callable[[TypeCheckContext, object], TypeCheck]:
    def type_check_fn(_context, value: object) -> TypeCheck:
        if isinstance(value, VALID_DATAFRAME_CLASSES):
            try:
                # `lazy` instructs pandera to capture every (not just the first) validation error
                # TODO: pending alternative dataframe support
                if isinstance(schema, pa_pd.DataFrameSchema):
                    df = check.inst(value, pd.DataFrame, "Must be a pandas DataFrame.")
                    schema.validate(df, lazy=True)
                # need to check that polars and pandera.polars are available before isinstance
                elif pl and pa_pl and isinstance(schema, pa_pl.DataFrameSchema):
                    df = check.inst(value, pl.DataFrame, "Must be a polars DataFrame.")
                    schema.validate(df, lazy=True)
                else:
                    check.failed(
                        f"Unexpected schema/value type combination: {type(schema).__name__} / {type(value).__name__}"
                    )
            except pa_errors.SchemaErrors as e:
                return _pandera_errors_to_type_check(e, table_schema)
            except Exception as e:
                return TypeCheck(
                    success=False,
                    description=f"Unexpected error during validation: {e}",
                )
        else:
            return TypeCheck(
                success=False,
                description=(
                    f"Must be one of {VALID_DATAFRAME_CLASSES}, not {type(value).__name__}."
                ),
            )

        return TypeCheck(success=True)

    return type_check_fn


PANDERA_FAILURE_CASES_SCHEMA = TableSchema(
    columns=[
        TableColumn(
            name="schema_context",
            type="string",
            description="`Column` for column-wise checks, or `DataFrameSchema`",
        ),
        TableColumn(
            name="column",
            type="string",
            description="Column of value that failed the check, or `None` for wide checks.",
        ),
        TableColumn(
            name="check",
            type="string",
            description="Description of the failed Pandera check.",
        ),
        TableColumn(name="check_number", description="Index of the failed check."),
        TableColumn(
            name="failure_case",
            type="number | string",
            description="Value that failed a check.",
        ),
        TableColumn(
            name="index",
            type="number | string",
            description="Index (row) of value that failed a check.",
        ),
    ]
)


def _pandera_errors_to_type_check(
    error: pa_errors.SchemaErrors, _table_schema: TableSchema
) -> TypeCheck:
    return TypeCheck(
        success=False,
        description=str(error),
    )


def _pandera_schema_to_table_schema(schema: DagsterPanderaSchema) -> TableSchema:
    df_constraints = _pandera_schema_wide_checks_to_table_constraints(schema.checks)  # pyright: ignore[reportArgumentType]
    columns = [_pandera_column_to_table_column(col) for k, col in schema.columns.items()]
    return TableSchema(columns=columns, constraints=df_constraints)


def _pandera_schema_wide_checks_to_table_constraints(
    checks: Sequence[Union[pa.Check, pa.Hypothesis]],
) -> TableConstraints:
    return TableConstraints(other=[_pandera_check_to_table_constraint(check) for check in checks])


def _pandera_check_to_table_constraint(pa_check: Union[pa.Check, pa.Hypothesis]) -> str:
    return _get_pandera_check_identifier(pa_check)


def _pandera_column_to_table_column(pa_column: DagsterPanderaColumn) -> TableColumn:
    constraints = TableColumnConstraints(
        nullable=pa_column.nullable,
        unique=pa_column.unique,
        other=[_pandera_check_to_column_constraint(pa_check) for pa_check in pa_column.checks],
    )
    name = check.not_none(pa_column.name, "name")
    name = name if isinstance(name, str) else "/".join(name)
    return TableColumn(
        name=name,
        type=str(pa_column.dtype),
        description=pa_column.description,
        constraints=constraints,
    )


CHECK_OPERATORS = {
    "equal_to": "==",
    "not_equal_to": "!=",
    "less_than": "<",
    "less_than_or_equal_to": "<=",
    "greater_than": ">",
    "greater_than_or_equal_to": ">=",
}


def _extract_operand(error_str: str) -> str:
    match = re.search(r"(?<=\().+(?=\))", error_str)
    return match.group(0) if match else ""


def _pandera_check_to_column_constraint(pa_check: pa.Check) -> str:
    if pa_check.description:
        return pa_check.description
    elif pa_check.name in CHECK_OPERATORS:
        assert isinstance(pa_check.error, str), (
            "Expected pandera check to have string `error` attr."
        )
        return f"{CHECK_OPERATORS[pa_check.name]} {_extract_operand(pa_check.error)}"
    else:
        return _get_pandera_check_identifier(pa_check)


def _get_pandera_check_identifier(pa_check: Union[pa.Check, pa.Hypothesis]) -> str:
    return pa_check.description or pa_check.error or pa_check.name or str(pa_check)


__all__ = [
    "pandera_schema_to_dagster_type",
]
