import itertools
from typing import TYPE_CHECKING, Generator, Optional, Tuple, Type, Union

import dagster.check as check
import dask
import pandas as pd
import pandera as pa
from dagster import DagsterType, EventMetadataEntry, TypeCheck
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
        yield f"DagsterPanderaDataframe{i}"


_anonymous_type_name = _anonymous_type_name_func()

# ########################
# ##### PANDERA SCHEMA TO DAGSTER TYPE
# ########################


def pandera_schema_to_dagster_type(
    schema: Union[pa.DataFrameSchema, Type[pa.SchemaModel]],
    name: Optional[str] = None,
):

    if isinstance(schema, type) and issubclass(schema, pa.SchemaModel):
        name = name or schema.__name__
        schema = schema.to_schema()
    elif isinstance(schema, pa.DataFrameSchema):
        name = name or f"DagsterPanderaDataframe{next(_anonymous_type_name)}"
    else:
        raise TypeError("schema must be a pandera `DataFrameSchema` or a subclass of a pandera `SchemaModel`")

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
                        EventMetadataEntry.int(len(e.failure_cases), "Num failures"),
                        # TODO this will incorporate new Table event type
                        EventMetadataEntry.md(
                            e.failure_cases.head(10).to_markdown(), "Failure cases (first 10)"
                        ),
                    ],
                )
        else:
            return TypeCheck(
                success=False,
                description=f"Must be one of {VALIDATABLE_DATA_FRAME_CLASSES} not {type(value).__name__}.",
            )

        return TypeCheck(success=True)

    tschema = _pandera_schema_to_table_schema(schema)

    return DagsterType(
        type_check_fn=type_check_fn,
        name=name,
        description=schema.description,
        metadata_entries=[
            EventMetadataEntry.table_schema(tschema, label="schema"),
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
