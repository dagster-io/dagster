from collections import namedtuple

from dagster import check
from dagster.core.types.config import ConfigType

from .environment_configs import (
    construct_config_type_dictionary,
    define_environment_cls,
    EnvironmentClassCreationData,
)
from .pipeline import PipelineDefinition


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
    mode = check.opt_str_param(mode, 'mode', default=pipeline_def.get_default_mode_name())
    mode_definition = pipeline_def.get_mode_definition(mode)

    environment_cls = define_environment_cls(
        EnvironmentClassCreationData(
            pipeline_name=pipeline_def.name,
            solids=pipeline_def.solids,
            dependency_structure=pipeline_def.dependency_structure,
            mode_definition=mode_definition,
            logger_defs=mode_definition.loggers,
        )
    )

    environment_type = environment_cls.inst()

    config_type_dict_by_name, config_type_dict_by_key = construct_config_type_dictionary(
        pipeline_def.solid_defs, environment_type
    )

    return EnvironmentSchema(
        environment_type=environment_type,
        config_type_dict_by_name=config_type_dict_by_name,
        config_type_dict_by_key=config_type_dict_by_key,
    )


def create_environment_type(pipeline_def, mode=None):
    return create_environment_schema(pipeline_def, mode).environment_type
