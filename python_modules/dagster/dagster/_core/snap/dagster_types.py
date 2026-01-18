from collections.abc import Mapping, Sequence
from typing import NamedTuple, Optional

import dagster._check as check
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.metadata import (
    MetadataFieldSerializer,
    MetadataValue,
    normalize_metadata,
)
from dagster._core.types.dagster_type import DagsterType, DagsterTypeKind
from dagster._serdes import whitelist_for_serdes


def build_dagster_type_namespace_snapshot(
    pipeline_def: JobDefinition,
) -> "DagsterTypeNamespaceSnapshot":
    check.inst_param(pipeline_def, "pipeline_def", JobDefinition)
    return DagsterTypeNamespaceSnapshot(
        {dt.key: build_dagster_type_snap(dt) for dt in pipeline_def.all_dagster_types()}
    )


def build_dagster_type_snap(dagster_type: DagsterType) -> "DagsterTypeSnap":
    check.inst_param(dagster_type, "dagster_type", DagsterType)
    return DagsterTypeSnap(
        kind=dagster_type.kind,
        key=dagster_type.key,
        name=dagster_type.unique_name if dagster_type.has_unique_name else None,
        display_name=dagster_type.display_name,
        description=dagster_type.description,
        is_builtin=dagster_type.is_builtin,
        type_param_keys=dagster_type.type_param_keys,
        loader_schema_key=dagster_type.loader_schema_key,
        metadata=dagster_type.metadata,
    )


@whitelist_for_serdes
class DagsterTypeNamespaceSnapshot(
    NamedTuple(
        "_DagsterTypeNamespaceSnapshot",
        [("all_dagster_type_snaps_by_key", Mapping[str, "DagsterTypeSnap"])],
    )
):
    def __new__(cls, all_dagster_type_snaps_by_key: Mapping[str, "DagsterTypeSnap"]):
        return super().__new__(
            cls,
            all_dagster_type_snaps_by_key=check.mapping_param(
                all_dagster_type_snaps_by_key,
                "all_dagster_type_snaps_by_key",
                key_type=str,
                value_type=DagsterTypeSnap,
            ),
        )

    def get_dagster_type_snap(self, key: str) -> "DagsterTypeSnap":
        check.str_param(key, "key")
        return self.all_dagster_type_snaps_by_key[key]


@whitelist_for_serdes(
    skip_when_empty_fields={"metadata"},
    storage_field_names={"metadata": "metadata_entries"},
    field_serializers={"metadata": MetadataFieldSerializer},
)
class DagsterTypeSnap(
    NamedTuple(
        "_DagsterTypeSnap",
        [
            ("kind", DagsterTypeKind),
            ("key", str),
            ("name", Optional[str]),
            ("description", Optional[str]),
            ("display_name", str),
            ("is_builtin", bool),
            ("type_param_keys", Sequence[str]),
            ("loader_schema_key", Optional[str]),
            ("materializer_schema_key", Optional[str]),
            ("metadata", Mapping[str, MetadataValue]),
        ],
    )
):
    def __new__(
        cls,
        kind,
        key,
        name,
        description,
        display_name,
        is_builtin,
        type_param_keys,
        loader_schema_key=None,
        materializer_schema_key=None,
        metadata=None,
    ):
        return super().__new__(
            cls,
            kind=check.inst_param(kind, "kind", DagsterTypeKind),
            key=check.str_param(key, "key"),
            name=check.opt_str_param(name, "name"),
            display_name=check.str_param(display_name, "display_name"),
            description=check.opt_str_param(description, "description"),
            is_builtin=check.bool_param(is_builtin, "is_builtin"),
            type_param_keys=check.list_param(type_param_keys, "type_param_keys", of_type=str),
            loader_schema_key=check.opt_str_param(loader_schema_key, "loader_schema_key"),
            materializer_schema_key=check.opt_str_param(
                materializer_schema_key, "materializer_schema_key"
            ),
            metadata=normalize_metadata(
                check.opt_mapping_param(metadata, "metadata", key_type=str)
            ),
        )
