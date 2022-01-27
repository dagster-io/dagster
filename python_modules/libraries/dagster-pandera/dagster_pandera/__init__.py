import itertools
from typing import TYPE_CHECKING, Any, Dict, Generator, Optional, Tuple, Type, Union, cast

import dagster.check as check
import dask
import pandas as pd
import pandera as pa
from dagster import DagsterType, EventMetadataEntry, TypeCheck
from dagster.core.definitions.event_metadata import (
    TableMetadataEntryData,
    TableSchemaMetadataEntryData,
)
from dagster.core.definitions.event_metadata.table import (
    TableColumn,
    TableColumnConstraints,
    TableSchema,
)
from dagster.core.utils import check_dagster_package_version
from pkg_resources import Requirement
from pkg_resources import working_set as pkg_resources_available

from .version import __version__

if TYPE_CHECKING:
    import modin.pandas as mpd
    import databricks.koalas as ks

    # TODO
    # import dask
    # import ray
    ValidatableDataFrame = Union[pd.DataFrame, ks.DataFrame, mpd.DataFrame]

# TODO: Use TypedDict for description info (pending typing-extensions)

check_dagster_package_version("dagster-pandera", __version__)


def get_validatable_dataframe_classes() -> Tuple[type, ...]:
    classes = [pd.DataFrame]
    if pkg_resources_available.find(Requirement.parse("modin")) is not None:
        from modin.pandas import DataFrame as ModinDataFrame

        classes.append(ModinDataFrame)
    elif pkg_resources_available.find(Requirement.parse("koalas")) is not None:
        from databricks.koalas import DataFrame as KoalasDataFrame

        classes.append(KoalasDataFrame)
    return tuple(classes)


VALIDATABLE_DATA_FRAME_CLASSES = get_validatable_dataframe_classes()


def _anonymous_type_name_func() -> Generator[str, None, None]:
    for i in itertools.count(start=1):
        yield f"DagsterPandasDataframe{i}"


_anonymous_type_name = _anonymous_type_name_func()

# ########################
# ##### PANDERA SCHEMA TO DAGSTER TYPE
# ########################


def pandera_schema_to_dagster_type(
    schema: Union[pa.DataFrameSchema, Type[pa.SchemaModel]],
    name: Optional[str] = None,
    description: Optional[Union[str, Dict[str, Any]]] = None,
):

    if isinstance(schema, type) and issubclass(schema, pa.SchemaModel):
        name = name or schema.__name__
        schema = schema.to_schema()
    elif isinstance(schema, pa.DataFrameSchema):
        name = name or f"DagsterPanderaDataframe{next(_anonymous_type_name)}"
    else:
        raise TypeError("schema must be a DataFrameSchema or a subclass of SchemaModel")

    description = _normalize_schema_description(schema, description)

    def type_check_fn(_context, value: object) -> TypeCheck:
        if isinstance(value, VALIDATABLE_DATA_FRAME_CLASSES):
            try:
                # `lazy` instructs pandera to capture every (not just the first) validation error
                schema.validate(value, lazy=True)  # type: ignore [pandera type annotations wrong]
            except pa.errors.SchemaErrors as e:
                return TypeCheck(
                    success=False,
                    description=str(e),
                    metadata_entries=[
                        EventMetadataEntry.int(len(e.failure_cases), "num_failures"),
                        # TODO this will incorporate new Table event type
                        EventMetadataEntry.md(e.failure_cases.to_markdown(), "failure_cases"),
                    ],
                )
        else:
            return TypeCheck(
                success=False,
                description=f"Must be one of {VALIDATABLE_DATA_FRAME_CLASSES} not {type(value).__name__}.",
            )

        return TypeCheck(success=True)

    col_descs = cast(Dict[str, str], description.get("columns"))
    tschema = pandera_schema_to_table_schema(schema, col_descs)

    return DagsterType(
        type_check_fn=type_check_fn,
        name=name,
        description=description.get('summary'),
        metadata_entries=[
            EventMetadataEntry.text("foo", label="test"),
            EventMetadataEntry.table_schema(tschema, label="schema"),
        ],
    )

def _normalize_schema_description(schema: pa.DataFrameSchema, description: Optional[Union[str, Dict[str, Any]]]) -> Dict[str, Any]:
    if isinstance(description, str):
        return { 'summary': description }
    elif isinstance(description, dict):
        col_descs = description.get('columns', {})
        return {
            'summary': description.get('summary'),
            'columns': {
                k: col_descs.get(k) for k in schema.columns.keys()
            }
        }
    else:
        return { 'summary': None, 'columns': { k: None for k in schema.columns.keys() } }


# TODO: implement TableConstraints


def pandera_schema_to_table_schema(
    schema: pa.DataFrameSchema, column_descriptions: Dict[str, str]
) -> TableSchema:
    """Convert a pandera schema to a Dagster `TableSchema`.

    Args:
        schema (pa.DataFrameSchema): The pandera schema to convert.

    Returns:
        TableSchema: The converted table schema.
    """
    columns = [
        pandera_column_to_table_column(col, column_descriptions.get(cast(str, k), None))
        for k, col in schema.columns.items()
    ]
    return TableSchema(columns=columns)


def pandera_column_to_table_column(pa_column: pa.Column, description: Optional[str]) -> TableColumn:
    """Convert a pandera column to a dagster `TableColumn`.

    Args:
        column (pa.Column): The pandera column to convert.
        extra

    Returns:
        TableColumn: The converted table column.
    """
    constraints = TableColumnConstraints(
        nullable=pa_column.nullable,
        unique=pa_column.unique,
        other=[pandera_check_to_column_constraint(pa_check) for pa_check in pa_column.checks],
    )
    name = check.not_none(pa_column.name, "name")
    return TableColumn(
        name=name,
        type=str(pa_column.dtype),
        description=description,
        constraints=constraints,
    )


def pandera_check_to_column_constraint(pa_check: pa.Check) -> str:
    """Convert a pandera check to a descriptive string for inclusion in
    `TableColumnConstraints.other`.

    Args:
        check (pa.Check): The pandera check to convert.

    Returns:
        str: The descriptive string.
    """

    # `error` is the closest thing to a "description" offered by a pandera check
    return pa_check.error


__all__ = [
    "pandera_schema_to_dagster_type",
]
