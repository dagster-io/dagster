from collections import namedtuple

from dagster import check
from dagster.config.snap import ConfigFieldSnap, snap_from_field
from dagster.core.definitions import (
    CompositeSolidDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    SolidDefinition,
)
from dagster.serdes import whitelist_for_serdes

from .dep_snapshot import (
    DependencyStructureSnapshot,
    build_dep_structure_snapshot_from_icontains_solids,
)


def build_solid_definitions_snapshot(pipeline_def):
    check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
    return SolidDefinitionsSnapshot(
        solid_def_snaps=[
            build_core_solid_def_snap(solid_def)
            for solid_def in pipeline_def.all_solid_defs
            if isinstance(solid_def, SolidDefinition)
        ],
        composite_solid_def_snaps=[
            build_composite_solid_def_snap(solid_def)
            for solid_def in pipeline_def.all_solid_defs
            if isinstance(solid_def, CompositeSolidDefinition)
        ],
    )


@whitelist_for_serdes
class SolidDefinitionsSnapshot(
    namedtuple("_SolidDefinitionsSnapshot", "solid_def_snaps composite_solid_def_snaps")
):
    def __new__(cls, solid_def_snaps, composite_solid_def_snaps):
        return super(SolidDefinitionsSnapshot, cls).__new__(
            cls,
            solid_def_snaps=sorted(
                check.list_param(solid_def_snaps, "solid_def_snaps", of_type=SolidDefSnap),
                key=lambda solid_def: solid_def.name,
            ),
            composite_solid_def_snaps=sorted(
                check.list_param(
                    composite_solid_def_snaps,
                    "composite_solid_def_snaps",
                    of_type=CompositeSolidDefSnap,
                ),
                key=lambda comp_def: comp_def.name,
            ),
        )


def build_input_def_snap(input_def):
    check.inst_param(input_def, "input_def", InputDefinition)
    return InputDefSnap(
        name=input_def.name,
        dagster_type_key=input_def.dagster_type.key,
        description=input_def.description,
    )


def build_output_def_snap(output_def):
    check.inst_param(output_def, "output_def", OutputDefinition)
    return OutputDefSnap(
        name=output_def.name,
        dagster_type_key=output_def.dagster_type.key,
        description=output_def.description,
        is_required=output_def.is_required,
        is_dynamic=output_def.is_dynamic,
    )


def build_i_solid_def_snap(i_solid_def):
    return (
        build_composite_solid_def_snap(i_solid_def)
        if isinstance(i_solid_def, CompositeSolidDefinition)
        else build_core_solid_def_snap(i_solid_def)
    )


def build_composite_solid_def_snap(comp_solid_def):
    check.inst_param(comp_solid_def, "comp_solid_def", CompositeSolidDefinition)
    return CompositeSolidDefSnap(
        name=comp_solid_def.name,
        input_def_snaps=list(map(build_input_def_snap, comp_solid_def.input_defs)),
        output_def_snaps=list(map(build_output_def_snap, comp_solid_def.output_defs)),
        description=comp_solid_def.description,
        tags=comp_solid_def.tags,
        required_resource_keys=sorted(list(comp_solid_def.required_resource_keys)),
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
    check.inst_param(solid_def, "solid_def", SolidDefinition)
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


# This and a set of shared props helps implement a de facto mixin for
# Inheritance is quite difficult and counterintuitive in namedtuple land, so went with this scheme
# instead.
def _check_solid_def_header_args(
    name,
    input_def_snaps,
    output_def_snaps,
    description,
    tags,
    required_resource_keys,
    config_field_snap,
):
    return dict(
        name=check.str_param(name, "name"),
        input_def_snaps=check.list_param(input_def_snaps, "input_def_snaps", InputDefSnap),
        output_def_snaps=check.list_param(output_def_snaps, "output_def_snaps", OutputDefSnap),
        description=check.opt_str_param(description, "description"),
        tags=check.dict_param(tags, "tags"),  # validate using validate_tags?
        required_resource_keys=check.list_param(
            required_resource_keys, "required_resource_keys", str
        ),
        config_field_snap=check.opt_inst_param(
            config_field_snap, "config_field_snap", ConfigFieldSnap
        ),
    )


# shared impl for CompositeSolidDefSnap and SolidDefSnap
def _get_input_snap(solid_def, name):
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
def _get_output_snap(solid_def, name):
    check.str_param(name, "name")
    for out in solid_def.output_def_snaps:
        if out.name == name:
            return out

    check.failed(
        "Could not find output {output_name} in solid def {solid_def_name}".format(
            output_name=name, solid_def_name=solid_def.name
        )
    )


@whitelist_for_serdes
class CompositeSolidDefSnap(
    namedtuple(
        "_CompositeSolidDefSnap",
        "name input_def_snaps output_def_snaps description tags required_resource_keys "
        "config_field_snap dep_structure_snapshot input_mapping_snaps output_mapping_snaps",
    )
):
    def __new__(
        cls,
        name,
        input_def_snaps,
        output_def_snaps,
        description,
        tags,
        required_resource_keys,
        config_field_snap,
        dep_structure_snapshot,
        input_mapping_snaps,
        output_mapping_snaps,
    ):
        return super(CompositeSolidDefSnap, cls).__new__(
            cls,
            dep_structure_snapshot=check.inst_param(
                dep_structure_snapshot, "dep_structure_snapshot", DependencyStructureSnapshot
            ),
            input_mapping_snaps=check.list_param(
                input_mapping_snaps, "input_mapping_snaps", of_type=InputMappingSnap
            ),
            output_mapping_snaps=check.list_param(
                output_mapping_snaps, "output_mapping_snaps", of_type=OutputMappingSnap
            ),
            **_check_solid_def_header_args(
                name,
                input_def_snaps,
                output_def_snaps,
                description,
                tags,
                required_resource_keys,
                config_field_snap,
            ),
        )

    def get_input_mapping_snap(self, name):
        check.str_param(name, "name")
        for input_mapping_snap in self.input_mapping_snaps:
            if input_mapping_snap.external_input_name == name:
                return input_mapping_snap
        check.failed("Could not find input mapping snap named " + name)

    def get_output_mapping_snap(self, name):
        check.str_param(name, "name")
        for output_mapping_snap in self.output_mapping_snaps:
            if output_mapping_snap.external_output_name == name:
                return output_mapping_snap
        check.failed("Could not find output mapping snap named " + name)

    def get_input_snap(self, name):
        return _get_input_snap(self, name)

    def get_output_snap(self, name):
        return _get_output_snap(self, name)


@whitelist_for_serdes
class SolidDefSnap(
    namedtuple(
        "_SolidDefMeta",
        "name input_def_snaps output_def_snaps description tags required_resource_keys "
        "config_field_snap",
    )
):
    def __new__(
        cls,
        name,
        input_def_snaps,
        output_def_snaps,
        description,
        tags,
        required_resource_keys,
        config_field_snap,
    ):
        return super(SolidDefSnap, cls).__new__(
            cls,
            **_check_solid_def_header_args(
                name,
                input_def_snaps,
                output_def_snaps,
                description,
                tags,
                required_resource_keys,
                config_field_snap,
            ),
        )

    def get_input_snap(self, name):
        return _get_input_snap(self, name)

    def get_output_snap(self, name):
        return _get_output_snap(self, name)


ISolidDefSnap = (CompositeSolidDefSnap, SolidDefSnap)


@whitelist_for_serdes
class InputDefSnap(namedtuple("_InputDefSnap", "name dagster_type_key description")):
    def __new__(cls, name, dagster_type_key, description):
        return super(InputDefSnap, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            dagster_type_key=check.str_param(dagster_type_key, "dagster_type_key"),
            description=check.opt_str_param(description, "description"),
        )


@whitelist_for_serdes
class OutputDefSnap(
    namedtuple("_OutputDefSnap", "name dagster_type_key description is_required is_dynamic")
):
    def __new__(cls, name, dagster_type_key, description, is_required, is_dynamic=False):
        return super(OutputDefSnap, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            dagster_type_key=check.str_param(dagster_type_key, "dagster_type_key"),
            description=check.opt_str_param(description, "description"),
            is_required=check.bool_param(is_required, "is_required"),
            is_dynamic=check.bool_param(is_dynamic, "is_dynamic"),
        )


@whitelist_for_serdes
class OutputMappingSnap(
    namedtuple("_OutputMappingSnap", "mapped_solid_name mapped_output_name external_output_name")
):
    def __new__(cls, mapped_solid_name, mapped_output_name, external_output_name):
        return super(OutputMappingSnap, cls).__new__(
            cls,
            mapped_solid_name=check.str_param(mapped_solid_name, "mapped_solid_name"),
            mapped_output_name=check.str_param(mapped_output_name, "mapped_output_name"),
            external_output_name=check.str_param(external_output_name, "external_output_name"),
        )


def build_output_mapping_snap(output_mapping):
    return OutputMappingSnap(
        mapped_solid_name=output_mapping.maps_from.solid_name,
        mapped_output_name=output_mapping.maps_from.output_name,
        external_output_name=output_mapping.definition.name,
    )


@whitelist_for_serdes
class InputMappingSnap(
    namedtuple("_InputMappingSnap", "mapped_solid_name mapped_input_name external_input_name")
):
    def __new__(cls, mapped_solid_name, mapped_input_name, external_input_name):
        return super(InputMappingSnap, cls).__new__(
            cls,
            mapped_solid_name=check.str_param(mapped_solid_name, "mapped_solid_name"),
            mapped_input_name=check.str_param(mapped_input_name, "mapped_input_name"),
            external_input_name=check.str_param(external_input_name, "external_input_name"),
        )


def build_input_mapping_snap(input_mapping):
    return InputMappingSnap(
        mapped_solid_name=input_mapping.maps_to.solid_name,
        mapped_input_name=input_mapping.maps_to.input_name,
        external_input_name=input_mapping.definition.name,
    )
