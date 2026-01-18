import json
import logging
import os
from collections.abc import Mapping
from typing import Any, Optional

from dotenv import dotenv_values
from typing_extensions import Self

from dagster._config import Field, Map, StringSource
from dagster._config.field_utils import Shape
from dagster._core.secrets.loader import SecretsLoader
from dagster._serdes import ConfigurableClass
from dagster._serdes.config_class import ConfigurableClassData


def get_env_var_dict(base_dir: str) -> dict[str, str]:
    env_file_path = os.path.join(base_dir, ".env")
    if not os.path.exists(env_file_path):
        return {}

    return {key: val for key, val in dotenv_values(env_file_path).items() if val is not None}


class PerProjectEnvFileLoader(SecretsLoader, ConfigurableClass):
    """Default secrets loader which loads additional env vars from a per-project .env file.

    Can be manually configured in the dagster.yaml file or implicitly set via the
    DAGSTER_PROJECT_ENV_FILE_PATHS environment variable.
    """

    def __init__(
        self,
        inst_data: Optional[ConfigurableClassData] = None,
        location_paths: Optional[Mapping[str, str]] = None,
    ):
        self._inst_data = inst_data
        self._location_paths = location_paths

    @classmethod
    def config_type(cls) -> Shape:
        return Shape(
            fields={
                "location_paths": Map(key_type=str, inner_type=str),
            },
        )

    def get_secrets_for_environment(self, location_name: Optional[str]) -> dict[str, str]:
        inst_data = self._inst_data

        location_paths = self._location_paths or {}
        if not inst_data:
            inst_data_env = os.getenv("DAGSTER_PROJECT_ENV_FILE_PATHS")
            if inst_data_env:
                location_paths = json.loads(inst_data_env)
        else:
            location_paths = inst_data.config_dict.get("location_paths", {})

        if location_name and location_name in location_paths:
            env_file_path = os.path.join(os.getcwd(), location_paths[location_name])
            return get_env_var_dict(env_file_path)
        else:
            return {}

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return cls(inst_data=inst_data, **config_value)


class EnvFileLoader(SecretsLoader, ConfigurableClass):
    def __init__(
        self,
        inst_data: Optional[ConfigurableClassData] = None,
        base_dir=None,
    ):
        self._inst_data = inst_data
        self._base_dir = base_dir or os.getcwd()

    def get_secrets_for_environment(self, location_name: Optional[str]) -> dict[str, str]:
        env_file_path = os.path.join(self._base_dir, ".env")

        env_var_dict = get_env_var_dict(env_file_path)

        if len(env_var_dict):
            logging.getLogger("dagster").info(
                "Loaded environment variables from .env file: "
                + ",".join([env_var for env_var in env_var_dict]),
            )
        else:
            logging.getLogger("dagster").info("No environment variables in .env file")

        return env_var_dict

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {"base_dir": Field(StringSource, is_required=False)}

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return cls(inst_data=inst_data, **config_value)
