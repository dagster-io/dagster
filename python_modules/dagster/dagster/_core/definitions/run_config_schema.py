from typing import Iterable, Mapping, NamedTuple, Optional

import dagster._check as check
from dagster._config import ConfigType

from .config import ConfigMapping
from .pipeline_definition import PipelineDefinition


class RunConfigSchema(NamedTuple):
    run_config_schema_type: ConfigType
    config_type_dict_by_name: Mapping[str, ConfigType]
    config_type_dict_by_key: Mapping[str, ConfigType]
    config_mapping: Optional[ConfigMapping]

    def has_config_type(self, name: str) -> bool:
        check.str_param(name, "name")
        return name in self.config_type_dict_by_name

    def config_type_named(self, name: str) -> ConfigType:
        check.str_param(name, "name")
        return self.config_type_dict_by_name[name]

    def config_type_keyed(self, key: str) -> ConfigType:
        check.str_param(key, "key")
        return self.config_type_dict_by_key[key]

    def all_config_types(self) -> Iterable[ConfigType]:
        return self.config_type_dict_by_key.values()

    @property
    def config_type(self) -> ConfigType:
        if self.config_mapping:
            mapped_type = self.config_mapping.config_schema.config_type
            if mapped_type is None:
                check.failed("ConfigMapping config type unexpectedly None")
            return mapped_type

        return self.run_config_schema_type


def create_run_config_schema(
    pipeline_def: PipelineDefinition,
    mode: Optional[str] = None,
) -> RunConfigSchema:
    mode = check.opt_str_param(mode, "mode", default=pipeline_def.get_default_mode_name())

    return pipeline_def.get_run_config_schema(mode)
