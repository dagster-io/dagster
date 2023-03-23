from typing import Mapping, NamedTuple, Optional, Sequence, Union

import dagster._check as check
from dagster._config import ConfigFieldSnap, snap_from_field
from dagster._core.definitions import (
    GraphDefinition,
    InputDefinition,
    InputMapping,
    OpDefinition,
    OutputDefinition,
    OutputMapping,
    PipelineDefinition,
)
from dagster._core.definitions.metadata import (
    MetadataEntry,
)
from dagster._serdes import whitelist_for_serdes

from .dep_snapshot import (
    DependencyStructureSnapshot,
    build_dep_structure_snapshot_from_graph_def,
)


@whitelist_for_serdes(skip_when_empty_fields={"metadata_entries"})
class InputDefSnap(
    NamedTuple(
        "_InputDefSnap",
        [
            ("name", str),
            ("dagster_type_key", str),
            ("description", Optional[str]),
            ("metadata_entries", Sequence[MetadataEntry]),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        dagster_type_key: str,
        description: Optional[str],
        metadata_entries: Optional[Sequence[MetadataEntry]] = None,
    ):
        return super(InputDefSnap, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            dagster_type_key=check.str_param(dagster_type_key, "dagster_type_key"),
            description=check.opt_str_param(description, "description"),
            metadata_entries=check.opt_sequence_param(
                metadata_entries, "metadata_entries", of_type=MetadataEntry
            ),
        )


@whitelist_for_serdes(skip_when_empty_fields={"metadata_entries"})
class OutputDefSnap(
    NamedTuple(
        "_OutputDefSnap",
        [
            ("name", str),
            ("dagster_type_key", str),
            ("description", Optional[str]),
            ("is_required", bool),
            ("metadata_entries", Sequence[MetadataEntry]),
            ("is_dynamic", bool),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        dagster_type_key: str,
        description: Optional[str],
        is_required: bool,
        metadata_entries: Optional[Sequence[MetadataEntry]] = None,
        is_dynamic: bool = False,
    ):
        return super(OutputDefSnap, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            dagster_type_key=check.str_param(dagster_type_key, "dagster_type_key"),
            description=check.opt_str_param(description, "description"),
            is_required=check.bool_param(is_required, "is_required"),
            metadata_entries=check.opt_sequence_param(
                metadata_entries, "metadata_entries", of_type=MetadataEntry
            ),
            is_dynamic=check.bool_param(is_dynamic, "is_dynamic"),
        )


@whitelist_for_serdes
class OutputMappingSnap(
    NamedTuple(
        "_OutputMappingSnap",
        [
            ("mapped_solid_name", str),
            ("mapped_output_name", str),
            ("external_output_name", str),
        ],
    )
):
    def __new__(
        cls,
        mapped_solid_name: str,
        mapped_output_name: str,
        external_output_name: str,
    ):
        return super(OutputMappingSnap, cls).__new__(
            cls,
            mapped_solid_name=check.str_param(mapped_solid_name, "mapped_solid_name"),
            mapped_output_name=check.str_param(mapped_output_name, "mapped_output_name"),
            external_output_name=check.str_param(external_output_name, "external_output_name"),
        )


def build_output_mapping_snap(output_mapping: OutputMapping) -> OutputMappingSnap:
    return OutputMappingSnap(
        mapped_solid_name=output_mapping.maps_from.node_name,
        mapped_output_name=output_mapping.maps_from.output_name,
        external_output_name=output_mapping.graph_output_name,
    )


@whitelist_for_serdes(storage_field_names={"mapped_node_name": "mapped_solid_name"})
class InputMappingSnap(
    NamedTuple(
        "_InputMappingSnap",
        [
            ("mapped_node_name", str),
            ("mapped_input_name", str),
            ("external_input_name", str),
        ],
    )
):
    def __new__(cls, mapped_node_name: str, mapped_input_name: str, external_input_name: str):
        return super(InputMappingSnap, cls).__new__(
            cls,
            mapped_node_name=check.str_param(mapped_node_name, "mapped_node_name"),
            mapped_input_name=check.str_param(mapped_input_name, "mapped_input_name"),
            external_input_name=check.str_param(external_input_name, "external_input_name"),
        )


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
        metadata_entries=input_def.metadata_entries,
    )


def build_output_def_snap(output_def: OutputDefinition) -> OutputDefSnap:
    check.inst_param(output_def, "output_def", OutputDefinition)
    return OutputDefSnap(
        name=output_def.name,
        dagster_type_key=output_def.dagster_type.key,
        description=output_def.description,
        is_required=output_def.is_required,
        metadata_entries=output_def.metadata_entries,
        is_dynamic=output_def.is_dynamic,
    )


# This and a set of shared props helps implement a de facto mixin for
# Inheritance is quite difficult and counterintuitive in namedtuple land, so went with this scheme
# instead.
def _check_node_def_header_args(
    name: str,
    input_def_snaps: Sequence[InputDefSnap],
    output_def_snaps: Sequence[OutputDefSnap],
    description: Optional[str],
    tags: Mapping[str, str],
    config_field_snap: Optional[ConfigFieldSnap],
):
    return dict(
        name=check.str_param(name, "name"),
        input_def_snaps=check.sequence_param(input_def_snaps, "input_def_snaps", InputDefSnap),
        output_def_snaps=check.sequence_param(output_def_snaps, "output_def_snaps", OutputDefSnap),
        description=check.opt_str_param(description, "description"),
        tags=check.mapping_param(tags, "tags"),  # validate using validate_tags?
        config_field_snap=check.opt_inst_param(
            config_field_snap, "config_field_snap", ConfigFieldSnap
        ),
    )


@whitelist_for_serdes(storage_name="CompositeSolidDefSnap")
class GraphDefSnap(
    NamedTuple(
        "_GraphDefSnap",
        [
            ("name", str),
            ("input_def_snaps", Sequence[InputDefSnap]),
            ("output_def_snaps", Sequence[OutputDefSnap]),
            ("description", Optional[str]),
            ("tags", Mapping[str, object]),
            ("config_field_snap", Optional[ConfigFieldSnap]),
            ("dep_structure_snapshot", DependencyStructureSnapshot),
            ("input_mapping_snaps", Sequence[InputMappingSnap]),
            ("output_mapping_snaps", Sequence[OutputMappingSnap]),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        input_def_snaps: Sequence[InputDefSnap],
        output_def_snaps: Sequence[OutputDefSnap],
        description: Optional[str],
        tags: Mapping[str, str],
        config_field_snap: Optional[ConfigFieldSnap],
        dep_structure_snapshot: DependencyStructureSnapshot,
        input_mapping_snaps: Sequence[InputMappingSnap],
        output_mapping_snaps: Sequence[OutputMappingSnap],
    ):
        return super(GraphDefSnap, cls).__new__(
            cls,
            dep_structure_snapshot=check.inst_param(
                dep_structure_snapshot, "dep_structure_snapshot", DependencyStructureSnapshot
            ),
            input_mapping_snaps=check.sequence_param(
                input_mapping_snaps, "input_mapping_snaps", of_type=InputMappingSnap
            ),
            output_mapping_snaps=check.sequence_param(
                output_mapping_snaps, "output_mapping_snaps", of_type=OutputMappingSnap
            ),
            **_check_node_def_header_args(
                name,
                input_def_snaps,
                output_def_snaps,
                description,
                tags,
                config_field_snap,
            ),
        )

    def get_input_snap(self, name: str) -> InputDefSnap:
        return _get_input_snap(self, name)

    def get_output_snap(self, name: str) -> OutputDefSnap:
        return _get_output_snap(self, name)


@whitelist_for_serdes(storage_name="SolidDefSnap")
class OpDefSnap(
    NamedTuple(
        "_OpDefSnap",
        [
            ("name", str),
            ("input_def_snaps", Sequence[InputDefSnap]),
            ("output_def_snaps", Sequence[OutputDefSnap]),
            ("description", Optional[str]),
            ("tags", Mapping[str, object]),
            ("required_resource_keys", Sequence[str]),
            ("config_field_snap", Optional[ConfigFieldSnap]),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        input_def_snaps: Sequence[InputDefSnap],
        output_def_snaps: Sequence[OutputDefSnap],
        description: Optional[str],
        tags: Mapping[str, str],
        required_resource_keys: Sequence[str],
        config_field_snap: Optional[ConfigFieldSnap],
    ):
        return super(OpDefSnap, cls).__new__(
            cls,
            required_resource_keys=check.sequence_param(
                required_resource_keys, "required_resource_keys", str
            ),
            **_check_node_def_header_args(
                name,
                input_def_snaps,
                output_def_snaps,
                description,
                tags,
                config_field_snap,
            ),
        )

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
class NodeDefsSnap(
    NamedTuple(
        "_NodeDefsSnapshot",
        [
            ("op_def_snaps", Sequence[OpDefSnap]),
            ("graph_def_snaps", Sequence[GraphDefSnap]),
        ],
    )
):
    def __new__(
        cls,
        op_def_snaps: Sequence[OpDefSnap],
        graph_def_snaps: Sequence[GraphDefSnap],
    ):
        return super(NodeDefsSnap, cls).__new__(
            cls,
            op_def_snaps=sorted(
                check.sequence_param(op_def_snaps, "op_def_snaps", of_type=OpDefSnap),
                key=lambda solid_def: solid_def.name,
            ),
            graph_def_snaps=sorted(
                check.sequence_param(
                    graph_def_snaps,
                    "graph_def_snaps",
                    of_type=GraphDefSnap,
                ),
                key=lambda comp_def: comp_def.name,
            ),
        )


def build_node_defs_snap(pipeline_def: PipelineDefinition) -> NodeDefsSnap:
    check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
    solid_def_snaps = []
    graph_def_snaps = []
    for node_def in pipeline_def.all_node_defs:
        if isinstance(node_def, OpDefinition):
            solid_def_snaps.append(build_op_def_snap(node_def))
        elif isinstance(node_def, GraphDefinition):
            graph_def_snaps.append(build_graph_def_snap(node_def))
        else:
            check.failed(f"Unexpected NodeDefinition type {node_def}")

    return NodeDefsSnap(
        op_def_snaps=solid_def_snaps,
        # update when snapshot renames happen
        graph_def_snaps=graph_def_snaps,
    )


def build_graph_def_snap(graph_def: GraphDefinition) -> GraphDefSnap:
    check.inst_param(graph_def, "graph_def", GraphDefinition)
    return GraphDefSnap(
        name=graph_def.name,
        input_def_snaps=list(map(build_input_def_snap, graph_def.input_defs)),
        output_def_snaps=list(map(build_output_def_snap, graph_def.output_defs)),
        description=graph_def.description,
        tags=graph_def.tags,
        config_field_snap=snap_from_field(
            "config", graph_def.config_mapping.config_schema.as_field()
        )
        if graph_def.config_mapping
        and graph_def.config_mapping.config_schema
        and graph_def.config_mapping.config_schema.as_field()
        else None,
        dep_structure_snapshot=build_dep_structure_snapshot_from_graph_def(graph_def),
        input_mapping_snaps=list(map(build_input_mapping_snap, graph_def.input_mappings)),
        output_mapping_snaps=list(map(build_output_mapping_snap, graph_def.output_mappings)),
    )


def build_op_def_snap(op_def: OpDefinition) -> OpDefSnap:
    check.inst_param(op_def, "op_def", OpDefinition)
    return OpDefSnap(
        name=op_def.name,
        input_def_snaps=list(map(build_input_def_snap, op_def.input_defs)),
        output_def_snaps=list(map(build_output_def_snap, op_def.output_defs)),
        description=op_def.description,
        tags=op_def.tags,
        required_resource_keys=sorted(list(op_def.required_resource_keys)),
        config_field_snap=snap_from_field("config", op_def.config_field)
        if op_def.has_config_field
        else None,
    )


# shared impl for GraphDefSnap and OpDefSnap
def _get_input_snap(node_def: Union[GraphDefSnap, OpDefSnap], name: str) -> InputDefSnap:
    check.str_param(name, "name")
    for inp in node_def.input_def_snaps:
        if inp.name == name:
            return inp

    check.failed(f"Could not find input {name} in op def {node_def.name}")


# shared impl for GraphDefSnap and OpDefSnap
def _get_output_snap(node_def: Union[GraphDefSnap, OpDefSnap], name: str) -> OutputDefSnap:
    check.str_param(name, "name")
    for out in node_def.output_def_snaps:
        if out.name == name:
            return out

    check.failed(f"Could not find output {name} in solid def {node_def.name}")
