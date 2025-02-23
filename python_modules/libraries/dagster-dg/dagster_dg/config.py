from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Optional, TypedDict, TypeVar, cast

import click
import tomlkit
from click.core import ParameterSource

from dagster_dg.error import DgError, DgValidationError
from dagster_dg.utils import get_toml_value, is_macos, is_windows

T = TypeVar("T")

DEFAULT_BUILTIN_COMPONENT_LIB = "dagster_components"


def _get_default_cache_dir() -> Path:
    if is_windows():
        return Path.home() / "AppData" / "dg" / "cache"
    elif is_macos():
        return Path.home() / "Library" / "Caches" / "dg"
    else:
        return Path.home() / ".cache" / "dg"


DEFAULT_CACHE_DIR = _get_default_cache_dir()


@dataclass
class DgConfig:
    """Global configuration for Dg.

    Args:
        disable_cache (bool): If True, disable caching. Defaults to False.
        cache_dir (Optional[str]): The directory to use for caching. If None, the default cache will
            be used.
        verbose (bool): If True, log debug information.
        builitin_component_lib (str): The name of the builtin component library to load.
        use_dg_managed_environment (bool): If True, `dg` will build and manage a virtual environment
            using `uv`. Note that disabling the managed enviroment will also disable caching.
        require_local_venv (bool): If True, commands that access an environment with
            dagster-components will only use a `.venv` directory discovered in the ancestor tree. If no
            `.venv` directory is discovered, an error will be raised. Note that this disallows the use
            of both the system python environment and non-local but activated virtual environments.
    """

    disable_cache: bool = False
    cache_dir: Path = DEFAULT_CACHE_DIR
    verbose: bool = False
    builtin_component_lib: str = DEFAULT_BUILTIN_COMPONENT_LIB
    use_dg_managed_environment: bool = True
    require_local_venv: bool = True
    is_component_lib: bool = False
    is_project: bool = False
    is_workspace: bool = False
    root_package: Optional[str] = None
    component_package: Optional[str] = None
    component_lib_package: Optional[str] = None

    @classmethod
    def discover_config_file(
        cls,
        path: Path,
        predicate: Optional[Callable[[Mapping[str, Any]], bool]] = None,
    ) -> Optional[Path]:
        current_path = path.absolute()
        while True:
            config_path = current_path / "pyproject.toml"
            if config_path.exists() and is_dg_config_file(config_path, predicate):
                return config_path
            if current_path == current_path.parent:  # root
                return
            current_path = current_path.parent

    @classmethod
    def from_config_file(cls, path: Path) -> "DgConfig":
        current_config = load_dg_config_file(path)
        current_directory_path = path.parent
        while "extend" in current_config:
            extend_path = current_directory_path / current_config["extend"]
            if not is_dg_config_file(extend_path):
                raise DgValidationError(
                    "Config file {extend_path} was specified in `extend` field but does not contain a `tool.dg` section."
                )
            extend_config = load_dg_config_file(extend_path)
            current_config = cast(DgPartialFileConfig, {**extend_config, **current_config})
            current_directory_path = extend_path.parent
        return replace(DgConfig.default(), **current_config)

    @classmethod
    def default(cls) -> "DgConfig":
        return cls()


class DgPartialConfig(TypedDict, total=False):
    disable_cache: bool
    cache_dir: Path
    verbose: bool
    builtin_component_lib: str
    use_dg_managed_environment: bool
    require_local_venv: bool
    component_package: str
    component_lib_package: str
    is_project: bool
    is_component_lib: bool
    is_workspace: bool


def _normalize_dg_partial_config(raw_dict: Mapping[str, object]) -> DgPartialConfig:
    config = {**raw_dict}  # copy so we can modify it
    if "disable_cache" in config and not isinstance(config["disable_cache"], bool):
        raise DgValidationError("`disable_cache` must be a boolean.")
    if "cache_dir" in config:
        if not isinstance(config["cache_dir"], (Path, str)):
            raise DgValidationError("`cache_dir` must be a string.")
        elif isinstance(config["cache_dir"], str):
            config["cache_dir"] = Path(config["cache_dir"])
    if "verbose" in config and not isinstance(config["verbose"], bool):
        raise DgValidationError("`verbose` must be a boolean.")
    if "builtin_component_lib" in config and not isinstance(config["builtin_component_lib"], str):
        raise DgValidationError("`builtin_component_lib` must be a string.")
    if "use_dg_managed_environment" in config and not isinstance(
        config["use_dg_managed_environment"], bool
    ):
        raise DgValidationError("`use_dg_managed_environment` must be a boolean.")
    if "require_local_venv" in config and not isinstance(config["require_local_venv"], bool):
        raise DgValidationError("`require_local_venv` must be a boolean.")
    if "component_package" in config and not isinstance(config["component_package"], str):
        raise DgValidationError("`component_package` must be a string.")
    if "component_lib_package" in config and not isinstance(config["component_lib_package"], str):
        raise DgValidationError("`component_lib_package` must be a string.")
    if "is_project" in config and not isinstance(config["is_project"], bool):
        raise DgValidationError("`is_project` must be a boolean.")
    if "is_component_lib" in config and not isinstance(config["is_component_lib"], bool):
        raise DgValidationError("`is_component_lib` must be a boolean.")

    if "is_workspace" in config and not isinstance(config["is_workspace"], bool):
        raise DgValidationError("`is_workspace` must be a boolean.")

    if unrecognized_keys := [k for k in config.keys() if k not in DgPartialConfig.__annotations__]:
        raise DgValidationError(f"Unrecognized fields in configuration: {unrecognized_keys}")
    return cast(DgPartialConfig, config)


# ########################
# ##### CONFIG CLI OPTIONS
# ########################


def normalize_cli_config(
    cli_options: Mapping[str, object], cli_context: click.Context
) -> DgPartialConfig:
    # Remove any options that weren't explicitly provided.
    filtered_options = {
        key: value
        for key, value in cli_options.items()
        if cli_context.get_parameter_source(key) != ParameterSource.DEFAULT
    }
    return _normalize_dg_partial_config(filtered_options)


_CLI_CONTEXT_CONFIG_KEY = "config"


def set_config_on_cli_context(cli_context: click.Context, config: DgPartialConfig) -> None:
    cli_context.ensure_object(dict)
    cli_context.obj[_CLI_CONTEXT_CONFIG_KEY] = config


def has_config_on_cli_context(cli_context: click.Context) -> bool:
    return _CLI_CONTEXT_CONFIG_KEY in cli_context.ensure_object(dict)


def get_config_from_cli_context(cli_context: click.Context) -> DgPartialConfig:
    cli_context.ensure_object(dict)
    return cli_context.obj[_CLI_CONTEXT_CONFIG_KEY]


# ########################
# ##### CONFIG FILE LOADING
# ########################


class DgPartialFileConfig(DgPartialConfig, total=False):
    extend: str


def _validate_dg_partial_file_config(
    raw_dict: Mapping[str, object], file_path: Path
) -> DgPartialFileConfig:
    if "extend" in raw_dict:
        if not isinstance(raw_dict["extend"], str):
            _raise_file_config_validation_error("`extend` must be a string.", file_path)
        elif not (file_path.parent / raw_dict["extend"]).exists():
            _raise_file_config_validation_error(
                "Config specifies `extend` setting to non-existent file: {raw_dict['extend']}",
                file_path,
            )
    try:
        _normalize_dg_partial_config({k: v for k, v in raw_dict.items() if k not in ["extend"]})
    except DgValidationError as e:
        _raise_file_config_validation_error(str(e), file_path)
    return cast(DgPartialFileConfig, raw_dict)


def is_dg_config_file(
    path: Path, predicate: Optional[Callable[[Mapping[str, Any]], bool]] = None
) -> bool:
    toml = tomlkit.parse(path.read_text())
    return "dg" in toml.get("tool", {}) and (
        predicate(get_toml_value(toml, ["tool", "dg"], dict)) if predicate else True
    )


def load_dg_config_file(path: Path) -> DgPartialFileConfig:
    toml = tomlkit.parse(path.read_text())
    return _validate_dg_partial_file_config(get_toml_value(toml, ["tool", "dg"], dict), path)


def _raise_file_config_validation_error(message: str, file_path: Path) -> None:
    raise DgError(f"Error in configuration file {file_path}: {message}")
