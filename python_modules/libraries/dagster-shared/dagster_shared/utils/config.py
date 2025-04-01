import os
import sys
from pathlib import Path
from typing import Any

import tomlkit
import yaml


def is_windows() -> bool:
    return sys.platform == "win32"


def _get_default_dg_cli_file() -> Path:
    if is_windows():
        return Path.home() / "AppData" / "dg" / "dg.toml"
    else:
        return Path.home() / "dg.toml"


DEFAULT_DG_CLI_FILE = _get_default_dg_cli_file()


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
    return Path(os.getenv("DG_CLI_CONFIG", DEFAULT_DG_CLI_FILE))


def does_dg_config_file_exist() -> bool:
    return get_dg_config_path().exists()
