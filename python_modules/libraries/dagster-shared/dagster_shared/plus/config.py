import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

DEFAULT_CLOUD_CLI_FOLDER = os.path.join(os.path.expanduser("~"), ".dagster_cloud_cli")
DEFAULT_CLOUD_CLI_CONFIG = os.path.join(DEFAULT_CLOUD_CLI_FOLDER, "config")

DEFAULT_DG_CLI_FOLDER = os.path.join(os.path.expanduser("~"), ".dg")
DEFAULT_DG_CLI_CONFIG = os.path.join(DEFAULT_DG_CLI_FOLDER, "config")


@dataclass
class DagsterPlusCliConfig:
    organization: Optional[str] = None
    default_deployment: Optional[str] = None
    user_token: Optional[str] = None
    agent_timeout: Optional[int] = None

    @classmethod
    def from_file(cls, config_file: Path) -> "DagsterPlusCliConfig":
        contents = config_file.read_text()
        return cls(**yaml.safe_load(contents))

    def write_to_file(self, config_file: Path):
        config_file.write_text(yaml.dump({k: v for k, v in self.__dict__.items() if v is not None}))


def get_active_config_path() -> Path:
    cloud_config_path = get_dagster_cloud_cli_config_path()
    if cloud_config_path.exists():
        return cloud_config_path
    return get_dg_config_path()


def get_dg_config_path() -> Path:
    return Path(os.getenv("DG_CLI_CONFIG", DEFAULT_DG_CLI_CONFIG))


def get_dagster_cloud_cli_config_path() -> Path:
    return Path(os.getenv("DAGSTER_CLOUD_CLI_CONFIG", DEFAULT_CLOUD_CLI_CONFIG))
