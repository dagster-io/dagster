from collections.abc import Iterable, Mapping
from typing import NamedTuple, Optional

import dagster._check as check
from dagster._config import ConfigType
from dagster._core.definitions.config import ConfigMapping
from dagster._core.definitions.job_definition import JobDefinition


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
    job_def: JobDefinition,
) -> RunConfigSchema:
    return job_def.run_config_schema
