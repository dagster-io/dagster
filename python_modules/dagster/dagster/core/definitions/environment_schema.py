from collections import namedtuple

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.types.config import ConfigType, ALL_CONFIG_BUILTINS
from dagster.core.types.iterate_types import iterate_config_types

from .context import PipelineContextDefinition
from .environment_configs import define_environment_cls, EnvironmentClassCreationData
from .pipeline import PipelineDefinition
from .pipeline_creation import construct_runtime_type_dictionary
from .solid import SolidDefinition


def iterate_solid_def_types(solid_def):
    if solid_def.config_field:
        for runtime_type in iterate_config_types(solid_def.config_field.config_type):
            yield runtime_type


def _gather_all_schemas(solid_defs):
    runtime_types = construct_runtime_type_dictionary(solid_defs)
    for rtt in runtime_types.values():
        if rtt.input_schema:
            for ct in iterate_config_types(rtt.input_schema.schema_type):
                yield ct
        if rtt.output_schema:
            for ct in iterate_config_types(rtt.output_schema.schema_type):
                yield ct


def _gather_all_config_types(solid_defs, context_definitions, environment_type):
    check.list_param(solid_defs, 'solid_defs', SolidDefinition)
    check.dict_param(
        context_definitions,
        'context_definitions',
        key_type=str,
        value_type=PipelineContextDefinition,
    )

    check.inst_param(environment_type, 'environment_type', ConfigType)

    for solid_def in solid_defs:
        for runtime_type in iterate_solid_def_types(solid_def):
            yield runtime_type

    for context_definition in context_definitions.values():
        if context_definition.config_field:
            context_config_type = context_definition.config_field.config_type
            for runtime_type in iterate_config_types(context_config_type):
                yield runtime_type

    for runtime_type in iterate_config_types(environment_type):
        yield runtime_type


def construct_config_type_dictionary(solid_defs, context_definitions, environment_type):
    check.list_param(solid_defs, 'solid_defs', SolidDefinition)
    check.dict_param(
        context_definitions,
        'context_definitions',
        key_type=str,
        value_type=PipelineContextDefinition,
    )
    check.inst_param(environment_type, 'environment_type', ConfigType)

    type_dict_by_name = {t.name: t for t in ALL_CONFIG_BUILTINS}
    type_dict_by_key = {t.key: t for t in ALL_CONFIG_BUILTINS}
    all_types = list(
        _gather_all_config_types(solid_defs, context_definitions, environment_type)
    ) + list(_gather_all_schemas(solid_defs))

    for config_type in all_types:
        name = config_type.name
        if name and name in type_dict_by_name:
            if type(config_type) is not type(type_dict_by_name[name]):
                raise DagsterInvalidDefinitionError(
                    (
                        'Type names must be unique. You have constructed two different '
                        'instances of types with the same name "{name}".'
                    ).format(name=name)
                )
        elif name:
            type_dict_by_name[config_type.name] = config_type

        key = config_type.key

        if key in type_dict_by_key:
            if type(config_type) is not type(type_dict_by_key[key]):
                raise DagsterInvalidDefinitionError(
                    (
                        'Type keys must be unique. You have constructed two different '
                        'instances of types with the same key "{key}".'
                    ).format(key=key)
                )

        else:
            type_dict_by_key[config_type.key] = config_type

    return type_dict_by_name, type_dict_by_key


class EnvironmentSchema(
    namedtuple(
        '_EnvironmentSchema', 'environment_type config_type_dict_by_name config_type_dict_by_key'
    )
):
    def __new__(cls, environment_type, config_type_dict_by_name, config_type_dict_by_key):
        return super(EnvironmentSchema, cls).__new__(
            cls,
            environment_type=check.inst_param(environment_type, 'environment_type', ConfigType),
            config_type_dict_by_name=check.dict_param(
                config_type_dict_by_name,
                'config_type_dict_by_name',
                key_type=str,
                value_type=ConfigType,
            ),
            config_type_dict_by_key=check.dict_param(
                config_type_dict_by_key,
                'config_type_dict_by_key',
                key_type=str,
                value_type=ConfigType,
            ),
        )

    def has_config_type(self, name):
        check.str_param(name, 'name')
        return name in self.config_type_dict_by_name

    def config_type_named(self, name):
        check.str_param(name, 'name')
        return self.config_type_dict_by_name[name]

    def config_type_keyed(self, key):
        check.str_param(key, 'key')
        return self.config_type_dict_by_key[key]

    def all_config_types(self):
        return self.config_type_dict_by_key.values()


def create_environment_schema(pipeline_def, mode=None):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.opt_str_param(mode, 'mode')

    mode_definition = pipeline_def.get_mode_definition(mode)

    environment_cls = define_environment_cls(
        EnvironmentClassCreationData(
            pipeline_def.name,
            pipeline_def.solids,
            pipeline_def.context_definitions if mode_definition is None else None,
            pipeline_def.dependency_structure,
            mode_definition,
        )
    )

    environment_type = environment_cls.inst()

    config_type_dict_by_name, config_type_dict_by_key = construct_config_type_dictionary(
        pipeline_def.solid_defs, pipeline_def.context_definitions, environment_type
    )

    return EnvironmentSchema(
        environment_type=environment_type,
        config_type_dict_by_name=config_type_dict_by_name,
        config_type_dict_by_key=config_type_dict_by_key,
    )


def create_environment_type(pipeline_def, mode=None):
    return create_environment_schema(pipeline_def, mode).environment_type
