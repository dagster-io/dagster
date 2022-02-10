import itertools
from typing import TYPE_CHECKING, Callable, Generator, Optional, Tuple, Type, Union

import dagster.check as check
import dask
import pandas as pd
import pandera as pa
from dagster import DagsterType, EventMetadataEntry, TypeCheck
from dagster.core.definitions.event_metadata.table import (
    TableColumn,
    TableColumnConstraints,
    TableRecord,
    TableSchema,
)
from dagster.core.execution.context.system import TypeCheckContext
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

# TODO: pending alternative dataframe support
# from pkg_resources import Requirement
# from pkg_resources import working_set as pkg_resources_available


if TYPE_CHECKING:
    # TODO: pending alternative dataframe support
    # import modin.pandas as mpd
    # import databricks.koalas as ks
    # import dask
    # import ray
    ValidatableDataFrame = pd.DataFrame

check_dagster_package_version("dagster-pandera", __version__)

# ########################
# ##### VALID DATAFRAME CLASSES
# ########################

classes = [pd.DataFrame]

# TODO: pending alternative dataframe support
# if pkg_resources_available.find(Requirement.parse("modin")) is not None:
#     from modin.pandas import DataFrame as ModinDataFrame
#     classes.append(ModinDataFrame)
# elif pkg_resources_available.find(Requirement.parse("koalas")) is not None:
#     from databricks.koalas import DataFrame as KoalasDataFrame
#     classes.append(KoalasDataFrame)

VALID_DATAFRAME_CLASSES = tuple(classes)


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
    type_check_fn = _pandera_schema_to_type_check_fn(norm_schema)
    tschema = _pandera_schema_to_table_schema(norm_schema)

    return DagsterType(
        type_check_fn=type_check_fn,
        name=name,
        description=norm_schema.description,
        metadata_entries=[
            EventMetadataEntry.table_schema(tschema, label="schema"),
        ],
    )


def _anonymous_type_name_func() -> Generator[str, None, None]:
    for i in itertools.count(start=1):
        yield f"DagsterPanderaDataframe{i}"


_anonymous_type_name = _anonymous_type_name_func()


def _extract_name_from_pandera_schema(
    schema: Union[pa.DataFrameSchema, Type[pa.SchemaModel]],
) -> str:
    if isinstance(schema, type) and issubclass(schema, pa.SchemaModel):
        return schema.Config.title or schema.Config.name or schema.__name__
    elif isinstance(schema, pa.DataFrameSchema):
        return schema.title or schema.name or next(_anonymous_type_name)


def _pandera_schema_to_type_check_fn(
    schema: pa.DataFrameSchema,
) -> Callable[[TypeCheckContext, object], TypeCheck]:
    def type_check_fn(_context, value: object) -> TypeCheck:
        if isinstance(value, VALID_DATAFRAME_CLASSES):
            try:
                # `lazy` instructs pandera to capture every (not just the first) validation error
                schema.validate(value, lazy=True)
            except pa.errors.SchemaErrors as e:
                return _pandera_errors_to_type_check(e)
        else:
            return TypeCheck(
                success=False,
                description=f"Must be one of {VALID_DATAFRAME_CLASSES} not {type(value).__name__}.",
            )

        return TypeCheck(success=True)

    return type_check_fn


def _pandera_errors_to_type_check(error: pa.errors.SchemaErrors) -> TypeCheck:
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
        ],
    )


def _pandera_schema_to_table_schema(schema: pa.DataFrameSchema) -> TableSchema:
    columns = [_pandera_column_to_table_column(col) for k, col in schema.columns.items()]
    return TableSchema(columns=columns)


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


def _pandera_check_to_column_constraint(pa_check: pa.Check) -> str:
    return pa_check.description or pa_check.error


__all__ = [
    "pandera_schema_to_dagster_type",
]
