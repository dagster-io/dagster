from collections import namedtuple

from dagster import check
from dagster.core.definitions import InputDefinition, OutputDefinition, SolidDefinition
from dagster.core.serdes import whitelist_for_serdes

from .config_types import ConfigFieldMeta, meta_from_field


def build_input_def_meta(input_def):
    check.inst_param(input_def, 'input_def', InputDefinition)
    return InputDefMeta(
        name=input_def.name,
        dagster_type_key=input_def.dagster_type.key,
        description=input_def.description,
    )


def build_output_def_meta(output_def):
    check.inst_param(output_def, 'output_def', OutputDefinition)
    return OutputDefMeta(
        name=output_def.name,
        dagster_type_key=output_def.dagster_type.key,
        description=output_def.description,
        is_required=output_def.is_required,
    )


def build_solid_def_meta(solid_def):
    check.inst_param(solid_def, 'solid_def', SolidDefinition)
    return SolidDefMeta(
        name=solid_def.name,
        input_def_metas=list(map(build_input_def_meta, solid_def.input_defs)),
        output_def_metas=list(map(build_output_def_meta, solid_def.output_defs)),
        config_field_meta=meta_from_field('config', solid_def.config_field)
        if solid_def.config_field
        else None,
        description=solid_def.description,
        tags=solid_def.tags,
        required_resource_keys=list(solid_def.required_resource_keys),
        positional_inputs=solid_def.positional_inputs,
    )


@whitelist_for_serdes
class SolidDefMeta(
    namedtuple(
        '_SolidDefMeta',
        'name input_def_metas output_def_metas config_field_meta '
        'description tags required_resource_keys positional_inputs',
    )
):
    def __new__(
        cls,
        name,
        input_def_metas,
        output_def_metas,
        config_field_meta,
        description,
        tags,
        required_resource_keys,
        positional_inputs,
    ):
        return super(SolidDefMeta, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            input_def_metas=check.list_param(input_def_metas, 'input_def_metas', InputDefMeta),
            output_def_metas=check.list_param(output_def_metas, 'output_def_metas', OutputDefMeta),
            config_field_meta=check.opt_inst_param(
                config_field_meta, 'config_field_meta', ConfigFieldMeta
            ),
            description=check.opt_str_param(description, 'description'),
            tags=check.dict_param(tags, 'tags'),  # validate using validate_tags?
            required_resource_keys=check.list_param(
                required_resource_keys, 'required_resource_keys', str
            ),
            positional_inputs=check.list_param(positional_inputs, 'positional_inputs', str),
        )

    def get_input_meta(self, name):
        check.str_param(name, 'name')
        for inp in self.input_def_metas:
            if inp.name == name:
                return inp

        check.failed('Could not find input ' + name)

    def get_output_meta(self, name):
        check.str_param(name, 'name')
        for out in self.output_def_metas:
            if out.name == name:
                return out

        check.failed('Could not find output ' + name)


@whitelist_for_serdes
class InputDefMeta(namedtuple('_InputDefMeta', 'name dagster_type_key description')):
    def __new__(cls, name, dagster_type_key, description):
        return super(InputDefMeta, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            dagster_type_key=check.str_param(dagster_type_key, 'dagster_type_key'),
            description=check.opt_str_param(description, 'description'),
        )


@whitelist_for_serdes
class OutputDefMeta(namedtuple('_OutputDefMeta', 'name dagster_type_key description is_required')):
    def __new__(cls, name, dagster_type_key, description, is_required):
        return super(OutputDefMeta, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            dagster_type_key=check.str_param(dagster_type_key, 'dagster_type_key'),
            description=check.opt_str_param(description, 'description'),
            is_required=check.bool_param(is_required, 'is_required'),
        )
