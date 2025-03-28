from collections.abc import Mapping, Sequence
from functools import cached_property
from typing import AbstractSet, Any, Optional, Union, cast  # noqa: UP035

from dagster_shared.serdes.serdes import RecordSerializer

from dagster import _check as check
from dagster._config import (
    FIELD_NO_DEFAULT_PROVIDED,
    Array,
    ConfigEnumValueSnap,
    ConfigFieldSnap,
    ConfigSchemaSnapshot,
    ConfigType,
    ConfigTypeKind,
    ConfigTypeSnap,
    Enum,
    EnumValue,
    Field,
    Map,
    Noneable,
    Permissive,
    ScalarUnion,
    Selector,
    Shape,
    get_builtin_scalar_by_name,
)
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.metadata import (
    MetadataFieldSerializer,
    MetadataValue,
    RawMetadataValue,
    normalize_metadata,
)
from dagster._core.snap.config_types import build_config_schema_snapshot
from dagster._core.snap.dagster_types import (
    DagsterTypeNamespaceSnapshot,
    build_dagster_type_namespace_snapshot,
)
from dagster._core.snap.dep_snapshot import (
    DependencyStructureSnapshot,
    build_dep_structure_snapshot_from_graph_def,
)
from dagster._core.snap.mode import ModeDefSnap, build_mode_def_snap
from dagster._core.snap.node import (
    GraphDefSnap,
    NodeDefsSnapshot,
    OpDefSnap,
    build_node_defs_snapshot,
)
from dagster._core.utils import toposort_flatten
from dagster._record import IHaveNew, record, record_custom
from dagster._serdes import create_snapshot_id, deserialize_value, whitelist_for_serdes


def _create_job_snapshot_id(job_snap: "JobSnap"):
    return create_snapshot_id(job_snap)


class JobSnapSerializer(RecordSerializer["JobSnap"]):
    # v0
    # v1:
    #     - lineage added
    # v2:
    #     - graph_def_name
    # v3:
    #     - metadata added
    # v4:
    #     - add kwargs so that if future versions add new args, this version of deserialization will
    #     be able to ignore them. previously, new args would be passed to old versions and cause
    #     deserialization errors.
    # v5:
    #     - run_tags added
    def before_unpack(
        self,
        context,
        unpacked_dict: Any,
    ) -> dict[str, Any]:
        if unpacked_dict.get("graph_def_name") is None:
            unpacked_dict["graph_def_name"] = unpacked_dict["name"]
        if unpacked_dict.get("metadata") is None:
            unpacked_dict["metadata"] = []
        if unpacked_dict.get("lineage_snapshot") is None:
            unpacked_dict["lineage_snapshot"] = None
        if unpacked_dict.get("run_tags") is None:
            unpacked_dict["run_tags"] = None
        return unpacked_dict


# Note that unlike other serdes-whitelisted objects that hold metadata, the field here has always
# been called `metadata` instead of `metadata_entries`, so we don't need to rename the field for
# serialization.
@whitelist_for_serdes(
    storage_name="PipelineSnapshot",
    serializer=JobSnapSerializer,
    skip_when_empty_fields={"metadata"},
    skip_when_none_fields={"run_tags"},
    field_serializers={"metadata": MetadataFieldSerializer},
    storage_field_names={"node_defs_snapshot": "solid_definitions_snapshot"},
)
@record_custom
class JobSnap(IHaveNew):
    name: str
    description: Optional[str]
    tags: Mapping[str, Any]
    # It is important that run_tags is nullable to distinguish in host code between
    # snapshots from older code servers where run_tags does not exist as a field (and is
    # therefore None) vs snapshots from newer code servers where run_tags is always set, if
    # sometimes empty. In the None case, we need to set run_tags to tags (at the level of
    # ExternalJob) to maintain backcompat.
    run_tags: Optional[Mapping[str, Any]]
    config_schema_snapshot: ConfigSchemaSnapshot
    dagster_type_namespace_snapshot: DagsterTypeNamespaceSnapshot
    node_defs_snapshot: NodeDefsSnapshot
    dep_structure_snapshot: DependencyStructureSnapshot
    mode_def_snaps: Sequence[ModeDefSnap]
    lineage_snapshot: Optional["JobLineageSnap"]
    graph_def_name: str
    metadata: Mapping[str, MetadataValue]

    def __new__(
        cls,
        name: str,
        description: Optional[str],
        tags: Optional[Mapping[str, Any]],
        run_tags: Optional[Mapping[str, Any]],
        config_schema_snapshot: ConfigSchemaSnapshot,
        dagster_type_namespace_snapshot: DagsterTypeNamespaceSnapshot,
        node_defs_snapshot: NodeDefsSnapshot,
        dep_structure_snapshot: DependencyStructureSnapshot,
        mode_def_snaps: Sequence[ModeDefSnap],
        lineage_snapshot: Optional["JobLineageSnap"],
        graph_def_name: str,
        metadata: Optional[Mapping[str, RawMetadataValue]],
    ):
        return super().__new__(
            cls,
            name=name,
            description=description,
            tags=tags or {},
            run_tags=run_tags,
            config_schema_snapshot=config_schema_snapshot,
            dagster_type_namespace_snapshot=dagster_type_namespace_snapshot,
            node_defs_snapshot=node_defs_snapshot,
            dep_structure_snapshot=dep_structure_snapshot,
            mode_def_snaps=mode_def_snaps,
            lineage_snapshot=lineage_snapshot,
            graph_def_name=graph_def_name,
            metadata=normalize_metadata(
                check.opt_mapping_param(metadata, "metadata", key_type=str)
            ),
        )

    @classmethod
    def from_job_def(cls, job_def: JobDefinition) -> "JobSnap":
        check.inst_param(job_def, "job_def", JobDefinition)
        lineage = None
        if job_def.op_selection_data:
            lineage = JobLineageSnap(
                parent_snapshot_id=job_def.op_selection_data.parent_job_def.get_job_snapshot_id(),
                op_selection=sorted(job_def.op_selection_data.op_selection),
                resolved_op_selection=job_def.op_selection_data.resolved_op_selection,
            )
        if job_def.asset_selection_data:
            lineage = JobLineageSnap(
                parent_snapshot_id=job_def.asset_selection_data.parent_job_def.get_job_snapshot_id(),
                asset_selection=job_def.asset_selection_data.asset_selection,
                asset_check_selection=job_def.asset_selection_data.asset_check_selection,
            )

        return JobSnap(
            name=job_def.name,
            description=job_def.description,
            tags=job_def.tags,
            run_tags=job_def.run_tags if job_def.has_separately_defined_run_tags else None,
            metadata=job_def.metadata,
            config_schema_snapshot=build_config_schema_snapshot(job_def),
            dagster_type_namespace_snapshot=build_dagster_type_namespace_snapshot(job_def),
            node_defs_snapshot=build_node_defs_snapshot(job_def),
            dep_structure_snapshot=build_dep_structure_snapshot_from_graph_def(job_def.graph),
            mode_def_snaps=[build_mode_def_snap(job_def)],
            lineage_snapshot=lineage,
            graph_def_name=job_def.graph.name,
        )

    @cached_property
    def snapshot_id(self) -> str:
        return _create_job_snapshot_id(self)

    def get_node_def_snap(self, node_def_name: str) -> Union[OpDefSnap, GraphDefSnap]:
        check.str_param(node_def_name, "node_def_name")
        for node_def_snap in self.node_defs_snapshot.op_def_snaps:
            if node_def_snap.name == node_def_name:
                return node_def_snap

        for graph_def_snap in self.node_defs_snapshot.graph_def_snaps:
            if graph_def_snap.name == node_def_name:
                return graph_def_snap

        check.failed("not found")

    def has_node_name(self, node_name: str) -> bool:
        check.str_param(node_name, "node_name")
        for node_invocation_snap in self.dep_structure_snapshot.node_invocation_snaps:
            if node_invocation_snap.node_name == node_name:
                return True
        return False

    def get_config_type_from_node_def_snap(
        self,
        node_def_snap: Union[OpDefSnap, GraphDefSnap],
    ) -> Optional[ConfigType]:
        check.inst_param(node_def_snap, "node_def_snap", (OpDefSnap, GraphDefSnap))
        if node_def_snap.config_field_snap:
            config_type_key = node_def_snap.config_field_snap.type_key
            if self.config_schema_snapshot.has_config_snap(config_type_key):
                return construct_config_type_from_snap(
                    self.config_schema_snapshot.get_config_snap(config_type_key),
                    self.config_schema_snapshot.all_config_snaps_by_key,
                )
        return None

    @property
    def node_names(self) -> Sequence[str]:
        return [ss.node_name for ss in self.dep_structure_snapshot.node_invocation_snaps]

    @property
    def node_names_in_topological_order(self) -> Sequence[str]:
        upstream_outputs = {}

        for node_invocation_snap in self.dep_structure_snapshot.node_invocation_snaps:
            node_name = node_invocation_snap.node_name
            upstream_outputs[node_name] = {
                upstream_output_snap.node_name
                for input_dep_snap in node_invocation_snap.input_dep_snaps
                for upstream_output_snap in input_dep_snap.upstream_output_snaps
            }

        return toposort_flatten(upstream_outputs)


def _construct_enum_from_snap(config_type_snap: ConfigTypeSnap):
    enum_values = check.list_param(config_type_snap.enum_values, "enum_values", ConfigEnumValueSnap)

    return Enum(
        name=config_type_snap.key,
        enum_values=[
            EnumValue(enum_value_snap.value, description=enum_value_snap.description)
            for enum_value_snap in enum_values
        ],
    )


def _construct_fields(
    config_type_snap: ConfigTypeSnap,
    config_snap_map: Mapping[str, ConfigTypeSnap],
) -> Mapping[str, Field]:
    fields = check.not_none(config_type_snap.fields)
    return {
        cast(str, field.name): Field(
            construct_config_type_from_snap(config_snap_map[field.type_key], config_snap_map),
            description=field.description,
            is_required=field.is_required,
            default_value=(
                deserialize_value(cast(str, field.default_value_as_json_str))
                if field.default_provided
                else FIELD_NO_DEFAULT_PROVIDED
            ),
        )
        for field in fields
    }


def _construct_selector_from_snap(config_type_snap, config_snap_map):
    check.list_param(config_type_snap.fields, "config_field_snap", ConfigFieldSnap)

    return Selector(
        fields=_construct_fields(config_type_snap, config_snap_map),
        description=config_type_snap.description,
    )


def _construct_shape_from_snap(config_type_snap, config_snap_map):
    check.list_param(config_type_snap.fields, "config_field_snap", ConfigFieldSnap)

    return Shape(
        fields=_construct_fields(config_type_snap, config_snap_map),
        description=config_type_snap.description,
    )


def _construct_permissive_from_snap(config_type_snap, config_snap_map):
    check.opt_list_param(config_type_snap.fields, "config_field_snap", ConfigFieldSnap)

    return Permissive(
        fields=_construct_fields(config_type_snap, config_snap_map),
        description=config_type_snap.description,
    )


def _construct_scalar_union_from_snap(config_type_snap, config_snap_map):
    check.list_param(config_type_snap.type_param_keys, "type_param_keys", str)
    check.invariant(
        len(config_type_snap.type_param_keys) == 2,
        f"Expect SCALAR_UNION to provide a scalar key and a non scalar key. Snapshot Provided: {config_type_snap.type_param_keys}",
    )

    return ScalarUnion(
        scalar_type=construct_config_type_from_snap(
            config_snap_map[config_type_snap.type_param_keys[0]], config_snap_map
        ),
        non_scalar_schema=construct_config_type_from_snap(
            config_snap_map[config_type_snap.type_param_keys[1]], config_snap_map
        ),
    )


def _construct_array_from_snap(config_type_snap, config_snap_map):
    check.list_param(config_type_snap.type_param_keys, "type_param_keys", str)
    check.invariant(
        len(config_type_snap.type_param_keys) == 1,
        f"Expect ARRAY to provide a single inner type. Snapshot provided: {config_type_snap.type_param_keys}",
    )

    return Array(
        inner_type=construct_config_type_from_snap(
            config_snap_map[config_type_snap.type_param_keys[0]], config_snap_map
        )
    )


def _construct_map_from_snap(config_type_snap, config_snap_map):
    check.list_param(config_type_snap.type_param_keys, "type_param_keys", str)
    check.invariant(
        len(config_type_snap.type_param_keys) == 2,
        f"Expect map to provide exactly two types (key, value). Snapshot provided: {config_type_snap.type_param_keys}",
    )

    return Map(
        key_type=construct_config_type_from_snap(
            config_snap_map[config_type_snap.type_param_keys[0]],
            config_snap_map,
        ),
        inner_type=construct_config_type_from_snap(
            config_snap_map[config_type_snap.type_param_keys[1]],
            config_snap_map,
        ),
        # In a Map, the given_name stores the optional key_label_name
        key_label_name=config_type_snap.given_name,
    )


def _construct_noneable_from_snap(config_type_snap, config_snap_map):
    check.list_param(config_type_snap.type_param_keys, "type_param_keys", str)
    check.invariant(
        len(config_type_snap.type_param_keys) == 1,
        f"Expect NONEABLE to provide a single inner type. Snapshot provided: {config_type_snap.type_param_keys}",
    )
    return Noneable(
        construct_config_type_from_snap(
            config_snap_map[config_type_snap.type_param_keys[0]], config_snap_map
        )
    )


def construct_config_type_from_snap(
    config_type_snap: ConfigTypeSnap, config_snap_map: Mapping[str, ConfigTypeSnap]
) -> ConfigType:
    check.inst_param(config_type_snap, "config_type_snap", ConfigTypeSnap)
    check.mapping_param(config_snap_map, "config_snap_map", key_type=str, value_type=ConfigTypeSnap)

    if config_type_snap.kind in (ConfigTypeKind.SCALAR, ConfigTypeKind.ANY):
        return get_builtin_scalar_by_name(config_type_snap.key)
    elif config_type_snap.kind == ConfigTypeKind.ENUM:
        return _construct_enum_from_snap(config_type_snap)
    elif config_type_snap.kind == ConfigTypeKind.SELECTOR:
        return _construct_selector_from_snap(config_type_snap, config_snap_map)
    elif config_type_snap.kind == ConfigTypeKind.STRICT_SHAPE:
        return _construct_shape_from_snap(config_type_snap, config_snap_map)
    elif config_type_snap.kind == ConfigTypeKind.PERMISSIVE_SHAPE:
        return _construct_permissive_from_snap(config_type_snap, config_snap_map)
    elif config_type_snap.kind == ConfigTypeKind.SCALAR_UNION:
        return _construct_scalar_union_from_snap(config_type_snap, config_snap_map)
    elif config_type_snap.kind == ConfigTypeKind.ARRAY:
        return _construct_array_from_snap(config_type_snap, config_snap_map)
    elif config_type_snap.kind == ConfigTypeKind.MAP:
        return _construct_map_from_snap(config_type_snap, config_snap_map)
    elif config_type_snap.kind == ConfigTypeKind.NONEABLE:
        return _construct_noneable_from_snap(config_type_snap, config_snap_map)
    check.failed(f"Could not evaluate config type snap kind: {config_type_snap.kind}")


@whitelist_for_serdes(
    storage_name="PipelineSnapshotLineage",
    storage_field_names={
        "op_selection": "solid_selection",
        "resolved_op_selection": "solids_to_execute",
    },
)
@record
class JobLineageSnap:
    parent_snapshot_id: str
    op_selection: Optional[Sequence[str]] = None
    resolved_op_selection: Optional[AbstractSet[str]] = None
    asset_selection: Optional[AbstractSet[AssetKey]] = None
    asset_check_selection: Optional[AbstractSet[AssetCheckKey]] = None
