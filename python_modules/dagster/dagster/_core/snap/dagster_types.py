from typing import Dict, List, NamedTuple, Optional, Set

import dagster._check as check
from dagster._core.definitions.metadata import MetadataEntry
from dagster._core.definitions.pipeline_definition import PipelineDefinition
from dagster._core.types.dagster_type import DagsterType, DagsterTypeKind
from dagster._serdes import DefaultNamedTupleSerializer, whitelist_for_serdes


def build_dagster_type_namespace_snapshot(
    pipeline_def: PipelineDefinition,
) -> "DagsterTypeNamespaceSnapshot":
    check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
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
        materializer_schema_key=dagster_type.materializer_schema_key,
        metadata_entries=dagster_type.metadata_entries,
    )


@whitelist_for_serdes
class DagsterTypeNamespaceSnapshot(
    NamedTuple(
        "_DagsterTypeNamespaceSnapshot",
        [("all_dagster_type_snaps_by_key", Dict[str, "DagsterTypeSnap"])],
    )
):
    def __new__(cls, all_dagster_type_snaps_by_key: Dict[str, "DagsterTypeSnap"]):
        return super(DagsterTypeNamespaceSnapshot, cls).__new__(
            cls,
            all_dagster_type_snaps_by_key=check.dict_param(
                all_dagster_type_snaps_by_key,
                "all_dagster_type_snaps_by_key",
                key_type=str,
                value_type=DagsterTypeSnap,
            ),
        )

    def get_dagster_type_snap(self, key: str) -> "DagsterTypeSnap":
        check.str_param(key, "key")
        return self.all_dagster_type_snaps_by_key[key]


class DagsterTypeSnapSerializer(DefaultNamedTupleSerializer):
    @classmethod
    def skip_when_empty(cls) -> Set[str]:
        return {"metadata_entries"}  # Maintain stable snapshot ID for back-compat purposes


@whitelist_for_serdes(serializer=DagsterTypeSnapSerializer)
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
            ("type_param_keys", List[str]),
            ("loader_schema_key", Optional[str]),
            ("materializer_schema_key", Optional[str]),
            ("metadata_entries", List[MetadataEntry]),
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
        metadata_entries=None,
    ):
        return super(DagsterTypeSnap, cls).__new__(
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
            metadata_entries=check.opt_list_param(
                metadata_entries, "metadata_entries", of_type=MetadataEntry
            ),
        )
