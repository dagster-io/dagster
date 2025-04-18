from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Literal, TypedDict, Union, get_args

import dagster._check as check
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.metadata.table import (
    TableColumn as TableColumn,
    TableColumnConstraints as TableColumnConstraints,
    TableColumnDep as TableColumnDep,
    TableColumnLineage as TableColumnLineage,
    TableConstraints as TableConstraints,
    TableRecord as TableRecord,
    TableSchema as TableSchema,
)

if TYPE_CHECKING:
    from dagster._core.definitions.metadata import MetadataValue

InferrableExternalMetadataValue = Union[
    int, float, str, Mapping[str, Any], Sequence[Any], bool, None
]


class ExternalMetadataValue(TypedDict):
    type: "ExternalMetadataType"
    raw_value: InferrableExternalMetadataValue


# Infer the type from the raw value on the orchestration end
EXTERNAL_METADATA_TYPE_INFER = "__infer__"

ExternalMetadataType = Literal[
    "__infer__",
    "text",
    "url",
    "path",
    "notebook",
    "json",
    "md",
    "float",
    "int",
    "bool",
    "dagster_run",
    "asset",
    "null",
    "table",
    "table_schema",
    "table_column_lineage",
    "timestamp",
]
EXTERNAL_METADATA_VALUE_KEYS = frozenset(ExternalMetadataValue.__annotations__.keys())
EXTERNAL_METADATA_TYPES = frozenset(get_args(ExternalMetadataType))


def metadata_map_from_external(
    metadata: Mapping[str, ExternalMetadataValue],
) -> Mapping[str, "MetadataValue"]:
    return {k: metadata_value_from_external(v["raw_value"], v["type"]) for k, v in metadata.items()}


def metadata_value_from_external(
    value: Any, metadata_type: ExternalMetadataType
) -> "MetadataValue":
    from dagster._core.definitions.metadata import MetadataValue, normalize_metadata_value

    if metadata_type == EXTERNAL_METADATA_TYPE_INFER:
        return normalize_metadata_value(value)
    elif metadata_type == "text":
        return MetadataValue.text(value)
    elif metadata_type == "url":
        return MetadataValue.url(value)
    elif metadata_type == "path":
        return MetadataValue.path(value)
    elif metadata_type == "notebook":
        return MetadataValue.notebook(value)
    elif metadata_type == "json":
        return MetadataValue.json(value)
    elif metadata_type == "md":
        return MetadataValue.md(value)
    elif metadata_type == "float":
        return MetadataValue.float(value)
    elif metadata_type == "int":
        return MetadataValue.int(value)
    elif metadata_type == "bool":
        return MetadataValue.bool(value)
    elif metadata_type == "dagster_run":
        return MetadataValue.dagster_run(value)
    elif metadata_type == "asset":
        return MetadataValue.asset(AssetKey.from_user_string(value))
    elif metadata_type == "table":
        value = check.mapping_param(value, "table_value", key_type=str)
        return MetadataValue.table(
            records=[TableRecord(record) for record in value["records"]],
            schema=TableSchema(
                columns=[
                    TableColumn(
                        name=column["name"],
                        type=column["type"],
                        description=column.get("description"),
                        tags=column.get("tags"),
                        constraints=TableColumnConstraints(**column["constraints"])
                        if column.get("constraints")
                        else None,
                    )
                    for column in value["schema"]
                ]
            ),
        )
    elif metadata_type == "table_schema":
        value = check.mapping_param(value, "table_schema_value", key_type=str)
        return MetadataValue.table_schema(
            schema=TableSchema(
                columns=[
                    TableColumn(
                        name=column["name"],
                        type=column["type"],
                        description=column.get("description"),
                        tags=column.get("tags"),
                        constraints=TableColumnConstraints(**column["constraints"])
                        if column.get("constraints")
                        else None,
                    )
                    for column in value["columns"]
                ]
            )
        )
    elif metadata_type == "table_column_lineage":
        value = check.mapping_param(value, "table_column_value", key_type=str)
        return MetadataValue.column_lineage(
            lineage=TableColumnLineage(
                deps_by_column={
                    column: [TableColumnDep(**dep) for dep in deps]
                    for column, deps in value["deps_by_column"].items()
                }
            )
        )
    elif metadata_type == "timestamp":
        return MetadataValue.timestamp(float(check.numeric_param(value, "timestamp")))
    elif metadata_type == "null":
        return MetadataValue.null()
    else:
        check.failed(f"Unexpected metadata type {metadata_type}")
