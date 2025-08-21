import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable, Final, Optional

from typing_extensions import Literal, TypeAlias


def is_windows() -> bool:
    return sys.platform == "win32"


def get_default_dg_user_config_path() -> Path:
    if is_windows():
        return Path.home() / "AppData" / "dg" / "dg.toml"
    else:
        config_home = Path(os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config")))
        return config_home / "dg.toml"


def load_config(config_path: Path) -> dict[str, Any]:
    import tomlkit
    import yaml

    if config_path.suffix == ".toml":
        return tomlkit.parse(config_path.read_text()).unwrap()
    else:
        return yaml.safe_load(config_path.read_text()) or {}


def write_config(config_path: Path, config: dict[str, Any]):
    import tomlkit
    import yaml

    if config_path.suffix == ".toml":
        with open(config_path, "w") as f:
            tomlkit.dump(config, f)
    else:
        with open(config_path, "w") as f:
            yaml.safe_dump(config, f)


def get_dg_config_path() -> Path:
    return Path(os.getenv("DG_CLI_CONFIG", get_default_dg_user_config_path()))


def does_dg_config_file_exist() -> bool:
    return get_dg_config_path().exists()


# The format determines whether settings are nested under the `tool.dg` section
# (`pyproject.toml`) or not (`dg.toml`).
DgConfigFileFormat: TypeAlias = Literal["root", "nested"]
_DEFAULT_PROJECT_DEFS_SUBMODULE: Final = "defs"


def detect_dg_config_file_format(path: Path) -> DgConfigFileFormat:
    """Check if the file is a dg-specific toml file."""
    return "root" if path.name == "dg.toml" or path.name == ".dg.toml" else "nested"


def load_toml_as_dict(path: Path) -> dict[str, Any]:
    import tomlkit

    return tomlkit.parse(path.read_text()).unwrap()


def has_dg_file_config(
    path: Path, predicate: Optional[Callable[[Mapping[str, Any]], bool]] = None
) -> bool:
    toml = load_toml_as_dict(path)
    # `dg.toml` is a special case where settings are defined at the top level
    if detect_dg_config_file_format(path) == "root":
        node = toml
    else:
        if "dg" not in toml.get("tool", {}):
            return False
        node = toml["tool"]["dg"]
    return predicate(node) if predicate else True


# NOTE: The presence of dg.toml will cause pyproject.toml to be ignored for purposes of dg config.
def discover_config_file(
    path: Path,
    predicate: Optional[Callable[[Mapping[str, Any]], bool]] = None,
) -> Optional[Path]:
    current_path = path.absolute()
    while True:
        config_file = locate_dg_config_in_folder(current_path, predicate)
        if config_file:
            return config_file
        if current_path == current_path.parent:  # root
            return None
        current_path = current_path.parent


def locate_dg_config_in_folder(
    path: Path,
    predicate: Optional[Callable[[Mapping[str, Any]], bool]] = None,
) -> Optional[Path]:
    current_path = path.absolute()
    dg_toml_path = current_path / "dg.toml"
    pyproject_toml_path = current_path / "pyproject.toml"
    if dg_toml_path.exists() and has_dg_file_config(dg_toml_path, predicate):
        return dg_toml_path
    elif pyproject_toml_path.exists() and has_dg_file_config(pyproject_toml_path, predicate):
        return pyproject_toml_path
    return None


def get_canonical_defs_module_name(defs_module_name: Optional[str], root_module_name: str) -> str:
    return defs_module_name or f"{root_module_name}.{_DEFAULT_PROJECT_DEFS_SUBMODULE}"
