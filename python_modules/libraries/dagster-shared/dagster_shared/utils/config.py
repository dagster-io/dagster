import os
from pathlib import Path
from typing import Any

import tomlkit
import yaml

DEFAULT_DG_CLI_FOLDER = os.path.join(os.path.expanduser("~"), ".dg")
DEFAULT_DG_CLI_CONFIG = os.path.join(DEFAULT_DG_CLI_FOLDER, "config.toml")


def load_config(config_path: Path) -> dict[str, Any]:
    if config_path.suffix == ".toml":
        return tomlkit.parse(config_path.read_text()).unwrap()
    else:
        return yaml.safe_load(config_path.read_text()) or {}


def write_config(config_path: Path, config: dict[str, Any]):
    if config_path.suffix == ".toml":
        with open(config_path, "w") as f:
            tomlkit.dump(config, f)
    else:
        with open(config_path, "w") as f:
            yaml.safe_dump(config, f)


def get_dg_config_path() -> Path:
    return Path(os.getenv("DG_CLI_CONFIG", DEFAULT_DG_CLI_CONFIG))


def does_dg_config_file_exist() -> bool:
    return get_dg_config_path().exists()
