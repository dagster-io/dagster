from collections.abc import Mapping, Sequence, Set
from functools import cached_property
from typing import Optional, Union

import dagster._check as check
from dagster._config import ConfigFieldSnap, snap_from_field
from dagster._core.definitions import (
    GraphDefinition,
    InputDefinition,
    InputMapping,
    JobDefinition,
    OpDefinition,
    OutputDefinition,
    OutputMapping,
)
from dagster._core.definitions.metadata import (
    MetadataFieldSerializer,
    MetadataValue,
    normalize_metadata,
)
from dagster._core.snap.dep_snapshot import (
    DependencyStructureSnapshot,
    build_dep_structure_snapshot_from_graph_def,
)
from dagster._record import IHaveNew, record, record_custom
from dagster._serdes import whitelist_for_serdes
from dagster._utils.warnings import suppress_dagster_warnings


@whitelist_for_serdes(
    storage_field_names={"metadata": "metadata_entries"},
    field_serializers={"metadata": MetadataFieldSerializer},
    skip_when_empty_fields={"metadata"},
)
@record_custom
class InputDefSnap(IHaveNew):
    name: str
    dagster_type_key: str
    description: Optional[str]
    metadata: Mapping[str, MetadataValue]

    def __new__(
        cls,
        name: str,
        dagster_type_key: str,
        description: Optional[str],
        metadata: Optional[Mapping[str, MetadataValue]] = None,
    ):
        return super().__new__(
            cls,
            name=name,
            dagster_type_key=dagster_type_key,
            description=description,
            metadata=normalize_metadata(
                check.opt_mapping_param(metadata, "metadata", key_type=str), allow_invalid=True
            ),
        )


@whitelist_for_serdes(
    storage_field_names={"metadata": "metadata_entries"},
    field_serializers={"metadata": MetadataFieldSerializer},
    skip_when_empty_fields={"metadata"},
)
@record_custom
class OutputDefSnap(IHaveNew):
    name: str
    dagster_type_key: str
    description: Optional[str]
    is_required: bool
    metadata: Mapping[str, MetadataValue]
    is_dynamic: bool

    def __new__(
        cls,
        name: str,
        dagster_type_key: str,
        description: Optional[str],
        is_required: bool,
        metadata: Optional[Mapping[str, MetadataValue]] = None,
        is_dynamic: bool = False,
    ):
        return super().__new__(
            cls,
            name=name,
            dagster_type_key=dagster_type_key,
            description=description,
            is_required=is_required,
            metadata=normalize_metadata(
                check.opt_mapping_param(metadata, "metadata", key_type=str), allow_invalid=True
            ),
            is_dynamic=is_dynamic,
        )


@whitelist_for_serdes(storage_field_names={"mapped_node_name": "mapped_solid_name"})
@record
class OutputMappingSnap:
    mapped_node_name: str
    mapped_output_name: str
    external_output_name: str


def build_output_mapping_snap(output_mapping: OutputMapping) -> OutputMappingSnap:
    return OutputMappingSnap(
        mapped_node_name=output_mapping.maps_from.node_name,
        mapped_output_name=output_mapping.maps_from.output_name,
        external_output_name=output_mapping.graph_output_name,
    )


@whitelist_for_serdes(storage_field_names={"mapped_node_name": "mapped_solid_name"})
@record
class InputMappingSnap:
    mapped_node_name: str
    mapped_input_name: str
    external_input_name: str


def build_input_mapping_snap(input_mapping: InputMapping) -> InputMappingSnap:
    return InputMappingSnap(
        mapped_node_name=input_mapping.maps_to.node_name,
        mapped_input_name=input_mapping.maps_to.input_name,
        external_input_name=input_mapping.graph_input_name,
    )


def build_input_def_snap(input_def: InputDefinition) -> InputDefSnap:
    check.inst_param(input_def, "input_def", InputDefinition)
    return InputDefSnap(
        name=input_def.name,
        dagster_type_key=input_def.dagster_type.key,
        description=input_def.description,
        metadata=input_def.metadata,
    )


def build_output_def_snap(output_def: OutputDefinition) -> OutputDefSnap:
    check.inst_param(output_def, "output_def", OutputDefinition)
    return OutputDefSnap(
        name=output_def.name,
        dagster_type_key=output_def.dagster_type.key,
        description=output_def.description,
        is_required=output_def.is_required,
        metadata=output_def.metadata,
        is_dynamic=output_def.is_dynamic,
    )


@whitelist_for_serdes(storage_name="CompositeSolidDefSnap", skip_when_empty_fields={"pools"})
@record
class GraphDefSnap:
    name: str
    input_def_snaps: Sequence[InputDefSnap]
    output_def_snaps: Sequence[OutputDefSnap]
    description: Optional[str]
    tags: Mapping[str, str]
    config_field_snap: Optional[ConfigFieldSnap]
    dep_structure_snapshot: DependencyStructureSnapshot
    input_mapping_snaps: Sequence[InputMappingSnap]
    output_mapping_snaps: Sequence[OutputMappingSnap]
    pools: Set[str] = set()

    @cached_property
    def input_def_map(self) -> Mapping[str, InputDefSnap]:
        return {input_def.name: input_def for input_def in self.input_def_snaps}

    @cached_property
    def output_def_map(self) -> Mapping[str, OutputDefSnap]:
        return {output_def.name: output_def for output_def in self.output_def_snaps}

    def get_input_snap(self, name: str) -> InputDefSnap:
        return _get_input_snap(self, name)

    def get_output_snap(self, name: str) -> OutputDefSnap:
        return _get_output_snap(self, name)


@whitelist_for_serdes(storage_name="SolidDefSnap", skip_when_none_fields={"pool"})
@record
class OpDefSnap:
    name: str
    input_def_snaps: Sequence[InputDefSnap]
    output_def_snaps: Sequence[OutputDefSnap]
    description: Optional[str]
    tags: Mapping[str, str]
    required_resource_keys: Sequence[str]
    config_field_snap: Optional[ConfigFieldSnap]
    pool: Optional[str] = None

    @cached_property
    def input_def_map(self) -> Mapping[str, InputDefSnap]:
        return {input_def.name: input_def for input_def in self.input_def_snaps}

    @cached_property
    def output_def_map(self) -> Mapping[str, OutputDefSnap]:
        return {output_def.name: output_def for output_def in self.output_def_snaps}

    def get_input_snap(self, name: str) -> InputDefSnap:
        return _get_input_snap(self, name)

    def get_output_snap(self, name: str) -> OutputDefSnap:
        return _get_output_snap(self, name)


@whitelist_for_serdes(
    storage_name="SolidDefinitionsSnapshot",
    storage_field_names={
        "op_def_snaps": "solid_def_snaps",
        "graph_def_snaps": "composite_solid_def_snaps",
    },
)
@record
class NodeDefsSnapshot:
    op_def_snaps: Sequence[OpDefSnap]
    graph_def_snaps: Sequence[GraphDefSnap]


@suppress_dagster_warnings
def build_node_defs_snapshot(job_def: JobDefinition) -> NodeDefsSnapshot:
    check.inst_param(job_def, "job_def", JobDefinition)
    op_def_snaps = []
    graph_def_snaps = []
    for node_def in job_def.all_node_defs:
        if isinstance(node_def, OpDefinition):
            op_def_snaps.append(build_op_def_snap(node_def))
        elif isinstance(node_def, GraphDefinition):
            graph_def_snaps.append(build_graph_def_snap(node_def))
        else:
            check.failed(f"Unexpected NodeDefinition type {node_def}")

    return NodeDefsSnapshot(
        op_def_snaps=sorted(
            op_def_snaps,
            key=lambda op_def: op_def.name,
        ),
        graph_def_snaps=sorted(
            graph_def_snaps,
            key=lambda graph_def: graph_def.name,
        ),
    )


def _by_name(
    snap: Union[
        InputDefSnap,
        OutputDefSnap,
    ],
) -> str:
    return snap.name


def build_graph_def_snap(graph_def: GraphDefinition) -> GraphDefSnap:
    check.inst_param(graph_def, "graph_def", GraphDefinition)
    return GraphDefSnap(
        name=graph_def.name,
        input_def_snaps=sorted(map(build_input_def_snap, graph_def.input_defs), key=_by_name),
        output_def_snaps=sorted(map(build_output_def_snap, graph_def.output_defs), key=_by_name),
        description=graph_def.description,
        tags=graph_def.tags,
        config_field_snap=(
            snap_from_field("config", graph_def.config_mapping.config_schema.as_field())
            if graph_def.config_mapping
            and graph_def.config_mapping.config_schema
            and graph_def.config_mapping.config_schema.as_field()
            else None
        ),
        dep_structure_snapshot=build_dep_structure_snapshot_from_graph_def(graph_def),
        input_mapping_snaps=sorted(
            map(build_input_mapping_snap, graph_def.input_mappings),
            key=lambda in_map_snap: in_map_snap.external_input_name,
        ),
        output_mapping_snaps=sorted(
            map(build_output_mapping_snap, graph_def.output_mappings),
            key=lambda out_map_snap: out_map_snap.external_output_name,
        ),
        pools=graph_def.pools,
    )


def build_op_def_snap(op_def: OpDefinition) -> OpDefSnap:
    check.inst_param(op_def, "op_def", OpDefinition)
    return OpDefSnap(
        name=op_def.name,
        input_def_snaps=sorted(map(build_input_def_snap, op_def.input_defs), key=_by_name),
        output_def_snaps=sorted(map(build_output_def_snap, op_def.output_defs), key=_by_name),
        description=op_def.description,
        tags=op_def.tags,
        required_resource_keys=sorted(op_def.required_resource_keys),
        config_field_snap=(
            snap_from_field("config", op_def.config_field)  # type: ignore  # (possible none)
            if op_def.has_config_field
            else None
        ),
        pool=op_def.pool,
    )


# shared impl for GraphDefSnap and OpDefSnap
def _get_input_snap(node_def: Union[GraphDefSnap, OpDefSnap], name: str) -> InputDefSnap:
    check.str_param(name, "name")
    inp = node_def.input_def_map.get(name)
    if inp:
        return inp

    check.failed(f"Could not find input {name} in op def {node_def.name}")


# shared impl for GraphDefSnap and OpDefSnap
def _get_output_snap(node_def: Union[GraphDefSnap, OpDefSnap], name: str) -> OutputDefSnap:
    check.str_param(name, "name")
    inp = node_def.output_def_map.get(name)
    if inp:
        return inp

    check.failed(f"Could not find output {name} in node def {node_def.name}")
