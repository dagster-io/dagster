from collections import namedtuple

from dagster import check
from dagster.core.definitions import InputDefinition, OutputDefinition, SolidDefinition
from dagster.core.serdes import whitelist_for_serdes

from .config_types import ConfigFieldSnap, snap_from_field


def build_input_def_snap(input_def):
    check.inst_param(input_def, 'input_def', InputDefinition)
    return InputDefSnap(
        name=input_def.name,
        dagster_type_key=input_def.dagster_type.key,
        description=input_def.description,
    )


def build_output_def_snap(output_def):
    check.inst_param(output_def, 'output_def', OutputDefinition)
    return OutputDefSnap(
        name=output_def.name,
        dagster_type_key=output_def.dagster_type.key,
        description=output_def.description,
        is_required=output_def.is_required,
    )


def build_solid_def_snap(solid_def):
    check.inst_param(solid_def, 'solid_def', SolidDefinition)
    return SolidDefSnap(
        name=solid_def.name,
        input_def_snaps=list(map(build_input_def_snap, solid_def.input_defs)),
        output_def_snaps=list(map(build_output_def_snap, solid_def.output_defs)),
        config_field_snap=snap_from_field('config', solid_def.config_field)
        if solid_def.config_field
        else None,
        description=solid_def.description,
        tags=solid_def.tags,
        required_resource_keys=list(solid_def.required_resource_keys),
        positional_inputs=solid_def.positional_inputs,
    )


@whitelist_for_serdes
class SolidDefSnap(
    namedtuple(
        '_SolidDefSnap',
        'name input_def_snaps output_def_snaps config_field_snap '
        'description tags required_resource_keys positional_inputs',
    )
):
    def __new__(
        cls,
        name,
        input_def_snaps,
        output_def_snaps,
        config_field_snap,
        description,
        tags,
        required_resource_keys,
        positional_inputs,
    ):
        return super(SolidDefSnap, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            input_def_snaps=check.list_param(input_def_snaps, 'input_def_snaps', InputDefSnap),
            output_def_snaps=check.list_param(output_def_snaps, 'output_def_snaps', OutputDefSnap),
            config_field_snap=check.opt_inst_param(
                config_field_snap, 'config_field_snap', ConfigFieldSnap
            ),
            description=check.opt_str_param(description, 'description'),
            tags=check.dict_param(tags, 'tags'),  # validate using validate_tags?
            required_resource_keys=check.list_param(
                required_resource_keys, 'required_resource_keys', str
            ),
            positional_inputs=check.list_param(positional_inputs, 'positional_inputs', str),
        )

    def get_input_snap(self, name):
        check.str_param(name, 'name')
        for inp in self.input_def_snaps:
            if inp.name == name:
                return inp

        check.failed('Could not find input ' + name)

    def get_output_snap(self, name):
        check.str_param(name, 'name')
        for out in self.output_def_snaps:
            if out.name == name:
                return out

        check.failed('Could not find output ' + name)


@whitelist_for_serdes
class InputDefSnap(namedtuple('_InputDefSnap', 'name dagster_type_key description')):
    def __new__(cls, name, dagster_type_key, description):
        return super(InputDefSnap, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            dagster_type_key=check.str_param(dagster_type_key, 'dagster_type_key'),
            description=check.opt_str_param(description, 'description'),
        )


@whitelist_for_serdes
class OutputDefSnap(namedtuple('_OutputDefSnap', 'name dagster_type_key description is_required')):
    def __new__(cls, name, dagster_type_key, description, is_required):
        return super(OutputDefSnap, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            dagster_type_key=check.str_param(dagster_type_key, 'dagster_type_key'),
            description=check.opt_str_param(description, 'description'),
            is_required=check.bool_param(is_required, 'is_required'),
        )
