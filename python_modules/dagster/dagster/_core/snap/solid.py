from typing import Mapping, NamedTuple, Optional, Sequence, Set, Union

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
from dagster._core.definitions.metadata import MetadataEntry, PartitionMetadataEntry
from dagster._serdes import whitelist_for_serdes
from dagster._serdes.serdes import DefaultNamedTupleSerializer

from .dep_snapshot import (
    DependencyStructureSnapshot,
    build_dep_structure_snapshot_from_icontains_solids,
)


class InputDefSnapSerializer(DefaultNamedTupleSerializer):
    @classmethod
    def skip_when_empty(cls) -> Set[str]:
        return {"metadata_entries"}  # Maintain stable snapshot ID for back-compat purposes


@whitelist_for_serdes(serializer=InputDefSnapSerializer)
class InputDefSnap(
    NamedTuple(
        "_InputDefSnap",
        [
            ("name", str),
            ("dagster_type_key", str),
            ("description", Optional[str]),
            ("metadata_entries", Sequence[Union[MetadataEntry, PartitionMetadataEntry]]),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        dagster_type_key: str,
        description: Optional[str],
        metadata_entries: Optional[Sequence[Union[MetadataEntry, PartitionMetadataEntry]]] = None,
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


class OutputDefSnapSerializer(DefaultNamedTupleSerializer):
    @classmethod
    def skip_when_empty(cls) -> Set[str]:
        return {"metadata_entries"}  # Maintain stable snapshot ID for back-compat purposes


@whitelist_for_serdes(serializer=OutputDefSnapSerializer)
class OutputDefSnap(
    NamedTuple(
        "_OutputDefSnap",
        [
            ("name", str),
            ("dagster_type_key", str),
            ("description", Optional[str]),
            ("is_required", bool),
            ("metadata_entries", Sequence[Union[MetadataEntry, PartitionMetadataEntry]]),
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
        mapped_solid_name=output_mapping.maps_from.solid_name,
        mapped_output_name=output_mapping.maps_from.output_name,
        external_output_name=output_mapping.graph_output_name,
    )


@whitelist_for_serdes
class InputMappingSnap(
    NamedTuple(
        "_InputMappingSnap",
        [
            ("mapped_solid_name", str),
            ("mapped_input_name", str),
            ("external_input_name", str),
        ],
    )
):
    def __new__(cls, mapped_solid_name: str, mapped_input_name: str, external_input_name: str):
        return super(InputMappingSnap, cls).__new__(
            cls,
            mapped_solid_name=check.str_param(mapped_solid_name, "mapped_solid_name"),
            mapped_input_name=check.str_param(mapped_input_name, "mapped_input_name"),
            external_input_name=check.str_param(external_input_name, "external_input_name"),
        )


def build_input_mapping_snap(input_mapping: InputMapping) -> InputMappingSnap:
    return InputMappingSnap(
        mapped_solid_name=input_mapping.maps_to.solid_name,
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
def _check_solid_def_header_args(
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


@whitelist_for_serdes
class CompositeSolidDefSnap(
    NamedTuple(
        "_CompositeSolidDefSnap",
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
        return super(CompositeSolidDefSnap, cls).__new__(
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
            **_check_solid_def_header_args(
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


@whitelist_for_serdes
class SolidDefSnap(
    NamedTuple(
        "_SolidDefMeta",
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
        return super(SolidDefSnap, cls).__new__(
            cls,
            required_resource_keys=check.sequence_param(
                required_resource_keys, "required_resource_keys", str
            ),
            **_check_solid_def_header_args(
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


@whitelist_for_serdes
class SolidDefinitionsSnapshot(
    NamedTuple(
        "_SolidDefinitionsSnapshot",
        [
            ("solid_def_snaps", Sequence[SolidDefSnap]),
            ("composite_solid_def_snaps", Sequence[CompositeSolidDefSnap]),
        ],
    )
):
    def __new__(
        cls,
        solid_def_snaps: Sequence[SolidDefSnap],
        composite_solid_def_snaps: Sequence[CompositeSolidDefSnap],
    ):
        return super(SolidDefinitionsSnapshot, cls).__new__(
            cls,
            solid_def_snaps=sorted(
                check.sequence_param(solid_def_snaps, "solid_def_snaps", of_type=SolidDefSnap),
                key=lambda solid_def: solid_def.name,
            ),
            composite_solid_def_snaps=sorted(
                check.sequence_param(
                    composite_solid_def_snaps,
                    "composite_solid_def_snaps",
                    of_type=CompositeSolidDefSnap,
                ),
                key=lambda comp_def: comp_def.name,
            ),
        )


def build_solid_definitions_snapshot(pipeline_def: PipelineDefinition) -> SolidDefinitionsSnapshot:
    check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
    solid_def_snaps = []
    graph_def_snaps = []
    for node_def in pipeline_def.all_node_defs:
        if isinstance(node_def, OpDefinition):
            solid_def_snaps.append(build_core_solid_def_snap(node_def))
        elif isinstance(node_def, GraphDefinition):
            graph_def_snaps.append(build_composite_solid_def_snap(node_def))
        else:
            check.failed(f"Unexpected NodeDefinition type {node_def}")

    return SolidDefinitionsSnapshot(
        solid_def_snaps=solid_def_snaps,
        # update when snapshot renames happen
        composite_solid_def_snaps=graph_def_snaps,
    )


def build_composite_solid_def_snap(comp_solid_def):
    check.inst_param(comp_solid_def, "comp_solid_def", GraphDefinition)
    return CompositeSolidDefSnap(
        name=comp_solid_def.name,
        input_def_snaps=list(map(build_input_def_snap, comp_solid_def.input_defs)),
        output_def_snaps=list(map(build_output_def_snap, comp_solid_def.output_defs)),
        description=comp_solid_def.description,
        tags=comp_solid_def.tags,
        config_field_snap=snap_from_field(
            "config", comp_solid_def.config_mapping.config_schema.as_field()
        )
        if comp_solid_def.config_mapping
        and comp_solid_def.config_mapping.config_schema
        and comp_solid_def.config_mapping.config_schema.as_field()
        else None,
        dep_structure_snapshot=build_dep_structure_snapshot_from_icontains_solids(comp_solid_def),
        input_mapping_snaps=list(map(build_input_mapping_snap, comp_solid_def.input_mappings)),
        output_mapping_snaps=list(map(build_output_mapping_snap, comp_solid_def.output_mappings)),
    )


def build_core_solid_def_snap(solid_def):
    check.inst_param(solid_def, "solid_def", OpDefinition)
    return SolidDefSnap(
        name=solid_def.name,
        input_def_snaps=list(map(build_input_def_snap, solid_def.input_defs)),
        output_def_snaps=list(map(build_output_def_snap, solid_def.output_defs)),
        description=solid_def.description,
        tags=solid_def.tags,
        required_resource_keys=sorted(list(solid_def.required_resource_keys)),
        config_field_snap=snap_from_field("config", solid_def.config_field)
        if solid_def.has_config_field
        else None,
    )


# shared impl for CompositeSolidDefSnap and SolidDefSnap
def _get_input_snap(
    solid_def: Union[CompositeSolidDefSnap, SolidDefSnap], name: str
) -> InputDefSnap:
    check.str_param(name, "name")
    for inp in solid_def.input_def_snaps:
        if inp.name == name:
            return inp

    check.failed(
        "Could not find input {input_name} in solid def {solid_def_name}".format(
            input_name=name, solid_def_name=solid_def.name
        )
    )


# shared impl for CompositeSolidDefSnap and SolidDefSnap
def _get_output_snap(
    solid_def: Union[CompositeSolidDefSnap, SolidDefSnap], name: str
) -> OutputDefSnap:
    check.str_param(name, "name")
    for out in solid_def.output_def_snaps:
        if out.name == name:
            return out

    check.failed(
        "Could not find output {output_name} in solid def {solid_def_name}".format(
            output_name=name, solid_def_name=solid_def.name
        )
    )
