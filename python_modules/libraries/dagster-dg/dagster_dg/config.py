import functools
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Any,
    Callable,
    Literal,
    Optional,
    TypedDict,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
)

import click
import tomlkit
import tomlkit.items
from click.core import ParameterSource
from typing_extensions import Never, NotRequired, Required, Self, TypeAlias, TypeGuard

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


def discover_workspace_root(path: Path) -> Optional[Path]:
    workspace_config_path = discover_config_file(
        path, lambda config: config["directory_type"] == "workspace"
    )
    return workspace_config_path.parent if workspace_config_path else None


def discover_config_file(
    path: Path,
    predicate: Optional[Callable[[Mapping[str, Any]], bool]] = None,
) -> Optional[Path]:
    current_path = path.absolute()
    while True:
        config_path = current_path / "pyproject.toml"
        if config_path.exists() and has_dg_file_config(config_path, predicate):
            return config_path
        if current_path == current_path.parent:  # root
            return
        current_path = current_path.parent


# NOTE: The set/has/get_config_from_cli_context is only used for the dynamically generated scaffold
# component commands. Hopefully we can get rid of it in the future.

_CLI_CONTEXT_CONFIG_KEY = "config"


def set_config_on_cli_context(cli_context: click.Context, config: "DgRawCliConfig") -> None:
    cli_context.ensure_object(dict)
    cli_context.obj[_CLI_CONTEXT_CONFIG_KEY] = config


def has_config_on_cli_context(cli_context: click.Context) -> bool:
    return _CLI_CONTEXT_CONFIG_KEY in cli_context.ensure_object(dict)


def get_config_from_cli_context(cli_context: click.Context) -> "DgRawCliConfig":
    cli_context.ensure_object(dict)
    return cli_context.obj[_CLI_CONTEXT_CONFIG_KEY]


# ########################
# ##### MAIN
# ########################


@dataclass
class DgConfig:
    cli: "DgCliConfig"
    project: Optional["DgProjectConfig"] = None
    workspace: Optional["DgWorkspaceConfig"] = None

    @classmethod
    def default(cls) -> Self:
        return cls(DgCliConfig.default())

    # Note that this function takes an argument called `container_workspace_file_config` instead of
    # just `workspace_file_config` because this is only to be passed when the root file config
    # points to a project inside of a workspace. If there is no package and the
    # root is itself a workspace, then `root_file_config` corresponds to the workspace and
    # `container_workspace_file_config` should be None.
    @classmethod
    def from_partial_configs(
        cls,
        root_file_config: Optional["DgFileConfig"] = None,
        container_workspace_file_config: Optional["DgWorkspaceFileConfig"] = None,
        command_line_config: Optional["DgRawCliConfig"] = None,
    ) -> Self:
        cli_partials: list[DgRawCliConfig] = []

        if container_workspace_file_config:
            if "cli" in container_workspace_file_config:
                cli_partials.append(container_workspace_file_config["cli"])
            workspace_config = DgWorkspaceConfig.from_raw(container_workspace_file_config)

        if root_file_config:
            if "cli" in root_file_config:
                cli_partials.append(root_file_config["cli"])

            if is_workspace_file_config(root_file_config):
                project_config = None
                workspace_config = DgWorkspaceConfig.from_raw(root_file_config["workspace"])
            elif is_project_file_config(root_file_config):
                project_config = DgProjectConfig.from_raw(root_file_config["project"])
                if not container_workspace_file_config:
                    workspace_config = None

        else:
            project_config = None
            workspace_config = None

        if command_line_config:
            cli_partials.append(command_line_config)
        cli_config = DgCliConfig.from_raw(*cli_partials) if cli_partials else DgCliConfig.default()

        return cls(cli_config, project_config, workspace_config)


# ########################
# ##### CLI
# ########################


@dataclass
class DgCliConfig:
    """CLI configuration for Dg.

    Args:
        disable_cache (bool): If True, disable caching. Defaults to False.
        cache_dir (Optional[str]): The directory to use for caching. If None, the default cache will
            be used.
        verbose (bool): If True, log debug information.
        use_component_modules (list[str]): Specify a list of modules containing components.
            Any components retrieved from the remote environment will be filtered to only include those
            from these modules. This is useful primarily for testing, as it allows targeting of a stable
            set of test components.
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
    use_component_modules: list[str] = field(default_factory=list)
    use_dg_managed_environment: bool = True
    require_local_venv: bool = True

    @classmethod
    def default(cls) -> Self:
        return cls()

    @classmethod
    def from_raw(cls, *partials: "DgRawCliConfig") -> Self:
        merged = cast("DgRawCliConfig", functools.reduce(lambda acc, x: {**acc, **x}, partials))  # type: ignore
        return cls(
            disable_cache=merged.get("disable_cache", DgCliConfig.disable_cache),
            cache_dir=Path(merged["cache_dir"]) if "cache_dir" in merged else DgCliConfig.cache_dir,
            verbose=merged.get("verbose", DgCliConfig.verbose),
            use_component_modules=merged.get(
                "use_component_modules",
                DgCliConfig.__dataclass_fields__["use_component_modules"].default_factory(),
            ),
            use_dg_managed_environment=merged.get(
                "use_dg_managed_environment", DgCliConfig.use_dg_managed_environment
            ),
            require_local_venv=merged.get("require_local_venv", DgCliConfig.require_local_venv),
        )


# All fields are optional
class DgRawCliConfig(TypedDict, total=False):
    disable_cache: bool
    cache_dir: str
    verbose: bool
    use_component_modules: Sequence[str]
    use_dg_managed_environment: bool
    require_local_venv: bool


# ########################
# ##### PROJECT
# ########################


@dataclass
class DgProjectConfig:
    root_module: str
    components_module: Optional[str] = None

    @classmethod
    def from_raw(cls, raw: "DgRawProjectConfig") -> Self:
        return cls(
            root_module=raw["root_module"],
            components_module=raw.get("components_module", DgProjectConfig.components_module),
        )


class DgRawProjectConfig(TypedDict):
    root_module: Required[str]
    components_module: NotRequired[str]


# ########################
# ##### WORKSPACE
# ########################


@dataclass
class DgWorkspaceConfig:
    pass

    @classmethod
    def from_raw(cls, raw: "DgRawWorkspaceConfig") -> Self:
        return cls()


class DgRawWorkspaceConfig(TypedDict):
    pass


# ########################
# ##### CLI CONFIG
# ########################


def normalize_cli_config(
    cli_options: Mapping[str, object], cli_context: click.Context
) -> DgRawCliConfig:
    # Remove any options that weren't explicitly provided.
    filtered_options = {
        key: value
        for key, value in cli_options.items()
        if cli_context.get_parameter_source(key) != ParameterSource.DEFAULT
    }
    return _validate_cli_config(filtered_options)


def _validate_cli_config(cli_opts: Mapping[str, object]) -> DgRawCliConfig:
    try:
        for key, type_ in DgRawCliConfig.__annotations__.items():
            _validate_cli_config_setting(cli_opts, key, type_)
        _validate_cli_config_no_extraneous_keys(cli_opts)
    except DgValidationError as e:
        _raise_cli_config_validation_error(str(e))
    return cast(DgRawCliConfig, cli_opts)


def _validate_cli_config_setting(cli_opts: Mapping[str, object], key: str, type_: type) -> None:
    if key in cli_opts and not _match_type(cli_opts[key], type_):
        raise DgValidationError(f"`{key}` must be a {type_.__name__}.")


def _validate_cli_config_no_extraneous_keys(cli_opts: Mapping[str, object]) -> None:
    extraneous_keys = [k for k in cli_opts.keys() if k not in DgRawCliConfig.__annotations__]
    if extraneous_keys:
        raise DgValidationError(f"Unrecognized fields: {extraneous_keys}")


def _raise_cli_config_validation_error(message: str) -> None:
    raise DgError(f"Error in CLI options: {message}")


# ########################
# ##### FILE CONFIG
# ########################

DgFileConfigDirectoryType = Literal["workspace", "project"]


class DgWorkspaceFileConfig(TypedDict):
    directory_type: Required[Literal["workspace"]]
    workspace: Required[DgRawWorkspaceConfig]
    cli: NotRequired[DgRawCliConfig]


def is_workspace_file_config(config: "DgFileConfig") -> TypeGuard[DgWorkspaceFileConfig]:
    return config["directory_type"] == "workspace"


class DgProjectFileConfig(TypedDict):
    directory_type: Required[Literal["project"]]
    project: Required[DgRawProjectConfig]
    cli: NotRequired[DgRawCliConfig]


def is_project_file_config(config: "DgFileConfig") -> TypeGuard[DgProjectFileConfig]:
    return config["directory_type"] == "project"


DgFileConfig: TypeAlias = Union[DgWorkspaceFileConfig, DgProjectFileConfig]


def has_dg_file_config(
    path: Path, predicate: Optional[Callable[[Mapping[str, Any]], bool]] = None
) -> bool:
    toml = tomlkit.parse(path.read_text())
    return "dg" in toml.get("tool", {}) and (
        predicate(get_toml_value(toml, ["tool", "dg"], dict)) if predicate else True
    )


def load_dg_root_file_config(path: Path) -> DgFileConfig:
    return _load_dg_file_config(path)


def load_dg_workspace_file_config(path: Path) -> "DgWorkspaceFileConfig":
    config = _load_dg_file_config(path)
    if is_workspace_file_config(config):
        return config
    else:
        _raise_file_config_validation_error("Expected a workspace configuration.", path)


def _load_dg_file_config(path: Path) -> DgFileConfig:
    toml = tomlkit.parse(path.read_text())
    raw_dict = get_toml_value(toml, ["tool", "dg"], tomlkit.items.Table).unwrap()
    try:
        config = _validate_dg_file_config({k: v for k, v in raw_dict.items()})
    except DgValidationError as e:
        _raise_file_config_validation_error(str(e), path)
    return config


def _validate_dg_file_config(raw_dict: Mapping[str, object]) -> DgFileConfig:
    _validate_file_config_setting(
        raw_dict,
        "directory_type",
        Required[Literal["workspace", "project"]],
        "tool.dg",
    )
    _validate_dg_config_file_cli_section(raw_dict.get("cli", {}))
    if raw_dict["directory_type"] == "workspace":
        _validate_file_config_setting(raw_dict, "workspace", dict, "tool.dg")
        _validate_file_config_workspace_section(raw_dict.get("workspace", {}))
        _validate_file_config_no_extraneous_keys(
            set(DgWorkspaceFileConfig.__annotations__.keys()), raw_dict, "tool.dg"
        )
        return cast(DgWorkspaceFileConfig, raw_dict)
    elif raw_dict["directory_type"] == "project":
        _validate_file_config_setting(raw_dict, "project", dict, "tool.dg")
        _validate_file_config_project_section(raw_dict.get("project", {}))
        _validate_file_config_no_extraneous_keys(
            set(DgProjectFileConfig.__annotations__.keys()), raw_dict, "tool.dg"
        )
        return cast(DgProjectFileConfig, raw_dict)
    else:
        raise DgError("Unreachable")


def _validate_dg_config_file_cli_section(section: object) -> None:
    if not isinstance(section, dict):
        raise DgValidationError("`tool.dg.cli` must be a table.")
    for key, type_ in DgRawCliConfig.__annotations__.items():
        _validate_file_config_setting(section, key, type_, "tool.dg.cli")
    _validate_file_config_no_extraneous_keys(
        set(DgRawCliConfig.__annotations__.keys()), section, "tool.dg.cli"
    )


def _validate_file_config_project_section(section: object) -> None:
    if not isinstance(section, dict):
        raise DgValidationError("`tool.dg.project` must be a table.")
    for key, type_ in DgRawProjectConfig.__annotations__.items():
        _validate_file_config_setting(section, key, type_, "tool.dg.project")
    _validate_file_config_no_extraneous_keys(
        set(DgRawProjectConfig.__annotations__.keys()), section, "tool.dg.project"
    )


def _validate_file_config_workspace_section(section: object) -> None:
    if not isinstance(section, dict):
        raise DgValidationError("`tool.dg.workspace` must be a table.")
    for key, type_ in DgRawWorkspaceConfig.__annotations__.items():
        _validate_file_config_setting(section, key, type_, "tool.dg.workspace")
    _validate_file_config_no_extraneous_keys(
        set(DgRawWorkspaceConfig.__annotations__.keys()), section, "tool.dg.workspace"
    )


def _validate_file_config_no_extraneous_keys(
    valid_keys: set[str], section: Mapping[str, object], toml_path: str
) -> None:
    extraneous_keys = [k for k in section.keys() if k not in valid_keys]
    if extraneous_keys:
        raise DgValidationError(f"Unrecognized fields in `{toml_path}`: {extraneous_keys}")


# expected_type Any to handle typing constructs (`Literal` etc)
def _validate_file_config_setting(
    section: Mapping[str, object],
    key: str,
    type_: Any,
    path_prefix: Optional[str] = None,
) -> None:
    origin = get_origin(type_)
    is_required = origin is Required
    class_ = type_ if origin not in (Required, NotRequired) else get_args(type_)[0]

    error_type = None
    if is_required and key not in section:
        error_type = "required"
    if key in section and not _match_type(section[key], class_):
        error_type = "mistype"
    if error_type:
        full_key = f"{path_prefix}.{key}" if path_prefix else key
        type_str = get_type_str(class_)
        if error_type == "required":
            _raise_missing_required_key_error(full_key, type_str)
        if error_type == "mistype":
            _raise_mistyped_key_error(full_key, type_str, section[key])


def _raise_missing_required_key_error(key: str, type_str: str) -> Never:
    raise DgValidationError(f"Missing required value for `{key}`. Expected {type_str}.")


def _raise_mistyped_key_error(key: str, type_str: str, value: object) -> Never:
    raise DgValidationError(f"`Invalid value for `{key}`. Expected {type_str}, got `{value}`.")


def _raise_file_config_validation_error(message: str, file_path: Path) -> Never:
    raise DgError(f"Error in configuration file {file_path}: {message}")


# expected_type Any to handle typing constructs (`Literal` etc)
def get_type_str(t: Any) -> str:
    origin = get_origin(t)
    if origin is None:
        # It's a builtin or normal class
        if hasattr(t, "__name__"):
            return t.__name__  # e.g. 'int', 'bool'
        return str(t)  # Fallback
    else:
        # It's a parametric type like list[str], Union[int, str], etc.
        args = get_args(t)
        arg_strs = [get_type_str(a) for a in args]
        if origin is Union:
            return " | ".join(arg_strs)
        if origin is Literal:
            arg_strs = [f'"{a}"' for a in arg_strs]
            return " | ".join(arg_strs)
        else:
            return f"{_get_origin_name(origin)}[{', '.join(arg_strs)}]"


def _get_origin_name(origin: Any) -> str:
    if origin is Sequence:
        return "Sequence"  # avoid the collections.abc prefix
    else:
        return origin.__name__


def _match_type(obj: object, type_: Any) -> bool:
    origin = get_origin(type_)
    # If typ is not a generic alias, do a normal isinstance check
    if origin is None:
        # Edge case: Union can appear as typing.Union without origin in older versions,
        # but with modern Python, get_origin should handle it.
        # If we get here, it's a concrete type like `int`, `str`, or type(None).
        return isinstance(obj, type_)

    # Handle Union (e.g. Union[int, str])
    if origin is Union:
        subtypes = get_args(type_)  # e.g. (int, str)
        return any(_match_type(obj, st) for st in subtypes)

    # Handle Literal (e.g. Literal[3, 5, "hello"])
    if origin is Literal:
        # get_args(typ) will be the allowed literal values
        allowed_values = get_args(type_)  # e.g. (3, 5, "hello")
        return obj in allowed_values

    # Handle list[...] (e.g. list[str])
    if origin is Sequence:
        (item_type,) = get_args(type_)  # e.g. (str,) for list[str]
        if not isinstance(obj, Sequence):
            return False
        return all(_match_type(item, item_type) for item in obj)

    # Handle list[...] (e.g. list[str])
    if origin is list:
        (item_type,) = get_args(type_)  # e.g. (str,) for list[str]
        if not isinstance(obj, list):
            return False
        return all(_match_type(item, item_type) for item in obj)

    # Handle tuple[...] (e.g. tuple[int, str], tuple[str, ...])
    if origin is tuple:
        arg_types = get_args(type_)
        if not isinstance(obj, tuple):
            return False
        # Distinguish fixed-length vs variable-length (ellipsis) tuples
        if len(arg_types) == 2 and arg_types[1] is Ellipsis:
            # e.g. tuple[str, ...]
            elem_type = arg_types[0]
            return all(_match_type(item, elem_type) for item in obj)
        else:
            # e.g. tuple[int, str, float]
            if len(obj) != len(arg_types):
                return False
            return all(_match_type(item, t) for item, t in zip(obj, arg_types))

    # Handle dict[...] (e.g. dict[str, int])
    if origin is dict:
        key_type, val_type = get_args(type_)
        if not isinstance(obj, dict):
            return False
        return all(_match_type(k, key_type) and _match_type(v, val_type) for k, v in obj.items())

    # Extend with other generic types (set, frozenset, etc.) if needed
    raise NotImplementedError(f"No handler for {type_}")
