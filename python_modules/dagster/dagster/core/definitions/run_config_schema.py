from typing import Dict, NamedTuple

from dagster import check
from dagster.config.config_type import ConfigType

from .pipeline import PipelineDefinition


class RunConfigSchema(NamedTuple):
    config_type: ConfigType
    config_type_dict_by_name: Dict[str, ConfigType]
    config_type_dict_by_key: Dict[str, ConfigType]

    def has_config_type(self, name):
        check.str_param(name, "name")
        return name in self.config_type_dict_by_name

    def config_type_named(self, name):
        check.str_param(name, "name")
        return self.config_type_dict_by_name[name]

    def config_type_keyed(self, key):
        check.str_param(key, "key")
        return self.config_type_dict_by_key[key]

    def all_config_types(self):
        return self.config_type_dict_by_key.values()


def create_run_config_schema(pipeline_def, mode=None):
    check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
    mode = check.opt_str_param(mode, "mode", default=pipeline_def.get_default_mode_name())

    return pipeline_def.get_run_config_schema(mode)


def create_run_config_schema_type(pipeline_def, mode=None):
    return create_run_config_schema(pipeline_def, mode).config_type
