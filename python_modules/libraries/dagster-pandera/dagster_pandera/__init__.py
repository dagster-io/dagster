import itertools
import textwrap
from typing import TYPE_CHECKING, Dict, Generator, Optional, Tuple, Type, Union
from pkg_resources import working_set as pkg_resources_available, Requirement
import pandera as pa
import pandas as pd
import dask
from dagster import DagsterType, EventMetadataEntry, TypeCheck
from dagster.core.definitions.event_metadata import ColumnarSchemaMetadataEntryData
from dagster.core.utils import check_dagster_package_version
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
        yield f"DagsterPandasDataframe{i}"


_anonymous_type_name = _anonymous_type_name_func()


def pandera_schema_to_dagster_type(
    schema: Union[pa.DataFrameSchema, Type[pa.SchemaModel]],
    name: Optional[str] = None,
    description: Optional[str] = None,
    column_descriptions: Dict[str, str] = None,
):

    if isinstance(schema, type) and issubclass(schema, pa.SchemaModel):
        name = name or schema.__name__
        schema = schema.to_schema()
    elif isinstance(schema, pa.DataFrameSchema):
        name = name or f"DagsterPanderaDataframe{next(_anonymous_type_name)}"
    else:
        raise TypeError("schema must be a DataFrameSchema or a subclass of SchemaModel")

    column_descriptions = column_descriptions or {}

    extra = {"columns": {k: {} for k in schema.columns.keys()}}
    for k, v in column_descriptions.items():
        extra["columns"][k]["description"] = v

    schema_desc = _build_schema_desc(schema, description, extra)

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

    fschema = pandera_schema_to_frictionless_schema(schema, extra)

    return DagsterType(
        type_check_fn=type_check_fn,
        name=name,
        description=schema_desc,
        metadata_entries=[
            EventMetadataEntry.text("foo", label="test"),
            EventMetadataEntry.columnar_schema(fschema, label="schema"),
        ],
    )


def _build_schema_desc(
    schema: pa.DataFrameSchema,
    desc: Optional[str],
    extra: Dict,
):
    sections = [
        "### Columns",
        "\n".join(
            [
                _build_column_desc(column, extra["columns"][k].get("description", None))
                for k, column in schema.columns.items()
            ]
        ),
    ]
    if desc:
        sections.insert(0, desc)
    return "\n\n".join(sections)


def _build_column_desc(column: pa.Column, desc: Optional[str]) -> str:
    head = f"- **{column.name}** [{column.dtype}]"
    if desc:
        head += f" {desc}"
    lines = [head]
    for check in column.checks:
        lines.append(textwrap.indent(_build_check_desc(check), "    "))
    return "\n".join(lines)


def _build_check_desc(_check) -> str:
    return "- check"


def pandera_schema_to_frictionless_schema(schema: pa.DataFrameSchema, extra: Dict) -> Dict:  # TODO
    """Convert a pandera schema to a frictionless schema.

    Args:
        schema (pa.DataFrameSchema): The pandera schema to convert.

    Returns:
        pa.DataFrameSchema: The frictionless schema.
    """
    fields = [
        pandera_column_to_frictionless_field(column, extra["columns"][column.name])
        for column in schema.columns.values()
    ]
    return {"fields": fields}


def pandera_column_to_frictionless_field(column: pa.Column, extra: Dict) -> Dict:  # TODO
    """Convert a pandera column to a frictionless field.

    Args:
        name (str): The name of the field.
        column (pa.Column): The pandera column to convert.

    Returns:
        Dict: The frictionless field.
    """
    field = {
        "name": column.name,
        "type": str(column.dtype),
        # "format": column.format,
        "description": extra.get("description"),
        "constraints": [pandera_check_to_frictionless_constraint(check) for check in column.checks],
    }
    field["constraints"].append({"required": column.nullable})
    field["constraints"].append({"unique": column.nullable})
    return field


def pandera_check_to_frictionless_constraint(check: pa.Check) -> Dict:  # TODO
    """Convert a pandera check to a frictionless constraint.

    Args:
        check (pa.Check): The pandera check to convert.

    Returns:
        Dict: The frictionless constraint.
    """
    return {
        "name": check.name,
        # "description": check.description,  # TODO
    }


__all__ = [
    "pandera_schema_to_dagster_type",
]
