import logging
import os
from typing import Dict, Optional

from dotenv import dotenv_values

import dagster._check as check
from dagster._config import Field, StringSource
from dagster._serdes import ConfigurableClass

from .loader import SecretsLoader


class EnvFileLoader(SecretsLoader, ConfigurableClass):
    def __init__(
        self,
        inst_data=None,
        base_dir=None,
    ):
        self._inst_data = inst_data
        self._base_dir = base_dir or os.getcwd()

    def get_secrets_for_environment(self, location_name: Optional[str]) -> Dict[str, str]:
        env_file_path = os.path.join(self._base_dir, ".env")

        if not os.path.exists(env_file_path):
            return {}

        env_var_dict: Dict[str, str] = {
            key: check.not_none(val)
            for key, val in dotenv_values(env_file_path).items()
            if val is not None
        }

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

    @staticmethod
    def from_config_value(inst_data, config_value):
        return EnvFileLoader(inst_data=inst_data, **config_value)
