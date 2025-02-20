from collections.abc import Mapping
from dataclasses import dataclass, fields, replace
from functools import partial
from pathlib import Path
from typing import Any, Callable, Literal, Optional, TypedDict, TypeVar, Union, cast

import click
import tomlkit
import tomlkit.items
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
    is_code_location: bool = False
    is_deployment: bool = False
    root_package: Optional[str] = None
    component_package: Optional[str] = None
    component_lib_package: Optional[str] = None
    code_locations: Optional[list["CodeLocationSpec"]] = None

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
    is_code_location: bool
    is_component_lib: bool
    is_deployment: bool
    code_locations: list["CodeLocationSpec"]


def _normalize_dg_partial_config(raw_dict: Mapping[str, object]) -> DgPartialConfig:
    config = {**raw_dict}  # copy so we can modify it

    _normalize_config_entry(config, "disable_cache", bool)
    _normalize_config_entry(config, "cache_dir", (str, Path), as_path=True)
    _normalize_config_entry(config, "verbose", bool)
    _normalize_config_entry(config, "builtin_component_lib", str)
    _normalize_config_entry(config, "use_dg_managed_environment", bool)
    _normalize_config_entry(config, "require_local_venv", bool)
    _normalize_config_entry(config, "component_package", str)
    _normalize_config_entry(config, "component_lib_package", str)
    _normalize_config_entry(config, "is_code_location", bool)
    _normalize_config_entry(config, "is_component_lib", bool)
    _normalize_config_entry(config, "is_deployment", bool)

    if "code_locations" in config:
        if not isinstance(config["code_locations"], list):
            raise DgValidationError("`code_locations` must be a list.")
        normalized_code_location_specs = []
        for spec in config["code_locations"]:
            if not isinstance(spec, dict):
                raise DgValidationError("`code_locations` must be a list of dictionaries.")
            normalized_code_location_specs.append(_normalize_code_location_spec(spec))
        config["code_locations"] = normalized_code_location_specs

    if unrecognized_keys := [k for k in config.keys() if k not in DgPartialConfig.__annotations__]:
        raise DgValidationError(f"Unrecognized fields in configuration: {unrecognized_keys}")
    return cast(DgPartialConfig, config)


def _normalize_config_entry(
    spec: dict[str, object],
    key: str,
    ttype: Union[type, tuple[type, ...]],
    is_required: bool = False,
    as_path: bool = False,
    error_prefix: str = "",
) -> None:
    types = ttype if isinstance(ttype, tuple) else (ttype,)
    type_str = " or ".join([t.__name__ for t in types])
    error_msg = f"{error_prefix}`{key}` must be a {type_str}."
    if key not in spec and is_required:
        raise DgValidationError(error_msg)
    elif key in spec:
        value = spec[key]
        if not isinstance(value, ttype):
            raise DgValidationError(error_msg)
        if as_path:
            if isinstance(value, Path):
                pass
            elif not isinstance(value, str):
                raise DgError(f"Only string paths are supported for {key}.")
            else:
                spec[key] = Path(value)


def _normalize_code_location_spec(raw_dict: Mapping[str, object]) -> "CodeLocationSpec":
    # copy so we can modify it-- replacing string paths with Path objects etc
    spec = {**raw_dict}

    if "type" not in spec:
        raise DgValidationError(
            "CodeLocationSpec `type` must be one of 'python_pointer', 'grpc_server'."
        )
    if spec["type"] == "python_pointer":
        return _normalize_python_pointer_code_location_spec(
            {k: v for k, v in spec.items() if k != "type"}
        )
    elif raw_dict["type"] == "grpc_server":
        return _normalize_grpc_server_code_location_spec(
            {k: v for k, v in spec.items() if k != "type"}
        )
    else:
        raise DgValidationError(
            "CodeLocationSpec `type` must be one of 'python_pointer', 'grpc_server'."
        )


def _normalize_python_pointer_code_location_spec(
    spec: dict[str, object],
) -> "PythonPointerCodeLocationSpec":
    _normalize_code_location_spec_entry(spec, "name", str, is_required=True)
    _normalize_code_location_spec_entry(spec, "module_name", str, is_required=False)
    _normalize_code_location_spec_entry(spec, "project_path", str, is_required=False)
    _normalize_code_location_spec_entry(spec, "attribute", str, is_required=False)
    _normalize_code_location_spec_entry(spec, "project_path", str, is_required=False, as_path=True)
    _normalize_code_location_spec_entry(spec, "module_path", str, is_required=False, as_path=True)
    _normalize_code_location_spec_entry(
        spec, "executable_path", str, is_required=False, as_path=True
    )

    if sum([1 for k in ["module_name", "project_path", "module_path"] if k in spec]) != 1:
        raise DgValidationError(
            "Exactly one of `module_name`, `project_path`, or `module_path` must be specified."
        )

    valid_fields = [f.name for f in fields(PythonPointerCodeLocationSpec)]
    if unrecognized_keys := [k for k in spec.keys() if k not in valid_fields]:
        raise DgValidationError(f"Unrecognized fields in configuration: {unrecognized_keys}")

    # Validation on the args performed above.
    return PythonPointerCodeLocationSpec(**spec)  # type: ignore


def _normalize_grpc_server_code_location_spec(
    spec: dict[str, object],
) -> "GrpcServerCodeLocationSpec":
    _normalize_code_location_spec_entry(spec, "name", str, is_required=True)
    _normalize_code_location_spec_entry(spec, "socket", str, is_required=False)
    _normalize_code_location_spec_entry(spec, "host", str, is_required=False)
    _normalize_code_location_spec_entry(spec, "port", int, is_required=False)

    if sum([1 for k in ["port", "socket"] if k in spec]) != 1:
        raise DgValidationError("Exactly one of `socket` or `port` must be specified.")

    valid_fields = [f.name for f in fields(GrpcServerCodeLocationSpec)]
    if unrecognized_keys := [k for k in spec.keys() if k not in valid_fields]:
        raise DgValidationError(f"Unrecognized fields in configuration: {unrecognized_keys}")

    # Validation on the args performed above.
    return GrpcServerCodeLocationSpec(**spec)  # type: ignore


_normalize_code_location_spec_entry = partial(
    _normalize_config_entry, error_prefix="CodeLocationSpec "
)

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
        normalized = _normalize_dg_partial_config(
            {k: v for k, v in raw_dict.items() if k not in ["extend"]}
        )
    except DgValidationError as e:
        _raise_file_config_validation_error(str(e), file_path)
    # Normalized will overwrite any values in raw_dict.
    return cast(DgPartialFileConfig, {**raw_dict, **normalized})


def is_dg_config_file(
    path: Path, predicate: Optional[Callable[[Mapping[str, Any]], bool]] = None
) -> bool:
    toml = tomlkit.parse(path.read_text()).unwrap()
    return "dg" in toml.get("tool", {}) and (predicate(toml["tool"]["dg"]) if predicate else True)


def load_dg_config_file(path: Path) -> DgPartialFileConfig:
    toml = tomlkit.parse(path.read_text())
    dg_section = get_toml_value(toml, ["tool", "dg"], tomlkit.items.Table).unwrap()
    return _validate_dg_partial_file_config(dg_section, path)


def _raise_file_config_validation_error(message: str, file_path: Path) -> None:
    raise DgError(f"Error in configuration file {file_path}: {message}")


# ########################
# ##### CODE LOCATION SPECIFICATION
# ########################


@dataclass
class RawCodeLocationSpec:
    name: str
    type: Literal["python_pointer", "grpc_server"]
    module_name: Optional[str] = None
    project_path: Optional[str] = None
    module_path: Optional[str] = None
    executable_path: Optional[str] = None
    attribute: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None


@dataclass
class CodeLocationSpec:
    name: str


@dataclass
class PythonPointerCodeLocationSpec(CodeLocationSpec):
    module_name: Optional[str] = None
    project_path: Optional[Path] = None
    module_path: Optional[Path] = None
    executable_path: Optional[Path] = None
    attribute: Optional[str] = None


@dataclass
class GrpcServerCodeLocationSpec(CodeLocationSpec):
    socket: Optional[str]
    host: Optional[str]
    port: Optional[int]
