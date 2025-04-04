import functools
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
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
from dagster_shared.plus.config import load_config
from dagster_shared.utils.config import get_dg_config_path
from typing_extensions import Never, NotRequired, Required, Self, TypeAlias, TypeGuard

from dagster_dg.error import DgError, DgValidationError
from dagster_dg.utils import (
    get_toml_node,
    has_toml_node,
    is_macos,
    is_windows,
    load_toml_as_dict,
    modify_toml,
)

T = TypeVar("T")


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


# NOTE: The presence of dg.toml will cause pyproject.toml to be ignored for purposes of dg config.
def discover_config_file(
    path: Path,
    predicate: Optional[Callable[[Mapping[str, Any]], bool]] = None,
) -> Optional[Path]:
    current_path = path.absolute()
    while True:
        dg_toml_path = current_path / "dg.toml"
        pyproject_toml_path = current_path / "pyproject.toml"
        if dg_toml_path.exists() and has_dg_file_config(dg_toml_path, predicate):
            return dg_toml_path
        elif pyproject_toml_path.exists() and has_dg_file_config(pyproject_toml_path, predicate):
            return pyproject_toml_path
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
        user_config: Optional["DgRawCliConfig"] = None,
    ) -> Self:
        cli_partials: list[DgRawCliConfig] = []

        if container_workspace_file_config:
            if "cli" in container_workspace_file_config:
                cli_partials.append(container_workspace_file_config["cli"])
            workspace_config = DgWorkspaceConfig.from_raw(
                container_workspace_file_config["workspace"]
            )

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

        all_cli_config = [user_config, *cli_partials] if user_config else cli_partials
        cli_config = (
            DgCliConfig.from_raw(*all_cli_config) if all_cli_config else DgCliConfig.default()
        )

        return cls(cli_config, project_config, workspace_config)  # pyright: ignore[reportPossiblyUnboundVariable]


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
    """

    disable_cache: bool = False
    cache_dir: Path = DEFAULT_CACHE_DIR
    verbose: bool = False
    use_component_modules: list[str] = field(default_factory=list)
    telemetry_enabled: bool = True

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
                cls.__dataclass_fields__["use_component_modules"].default_factory(),
            ),
            telemetry_enabled=merged.get("telemetry", {}).get(
                "enabled", DgCliConfig.telemetry_enabled
            ),
        )


class RawDgTelemetryConfig(TypedDict, total=False):
    enabled: bool


# All fields are optional
class DgRawCliConfig(TypedDict, total=False):
    disable_cache: bool
    cache_dir: str
    verbose: bool
    use_component_modules: Sequence[str]
    telemetry: RawDgTelemetryConfig


# ########################
# ##### PROJECT
# ########################

DgProjectPythonEnvironment: TypeAlias = Literal["active", "persistent_uv"]


@dataclass
class DgProjectConfig:
    root_module: str
    defs_module: Optional[str] = None
    code_location_target_module: Optional[str] = None
    code_location_name: Optional[str] = None
    python_environment: DgProjectPythonEnvironment = "active"

    @classmethod
    def from_raw(cls, raw: "DgRawProjectConfig") -> Self:
        return cls(
            root_module=raw["root_module"],
            defs_module=raw.get("defs_module", DgProjectConfig.defs_module),
            code_location_name=raw.get("code_location_name", DgProjectConfig.code_location_name),
            code_location_target_module=raw.get(
                "code_location_target_module",
                DgProjectConfig.code_location_target_module,
            ),
            python_environment=raw.get("python_environment", DgProjectConfig.python_environment),
        )


class DgRawProjectConfig(TypedDict):
    root_module: Required[str]
    defs_module: NotRequired[str]
    code_location_target_module: NotRequired[str]
    code_location_name: NotRequired[str]
    python_environment: NotRequired[DgProjectPythonEnvironment]


# ########################
# ##### WORKSPACE
# ########################


@dataclass
class DgWorkspaceConfig:
    projects: list["DgWorkspaceProjectSpec"]
    scaffold_project_options: "DgWorkspaceScaffoldProjectOptions"

    @classmethod
    def from_raw(cls, raw: "DgRawWorkspaceConfig") -> Self:
        projects = [DgWorkspaceProjectSpec.from_raw(spec) for spec in raw.get("projects", [])]
        scaffold_project_options = DgWorkspaceScaffoldProjectOptions.from_raw(
            raw.get("scaffold_project_options", {})
        )
        return cls(projects, scaffold_project_options)


class DgRawWorkspaceConfig(TypedDict, total=False):
    projects: list["DgRawWorkspaceProjectSpec"]
    scaffold_project_options: "DgRawWorkspaceNewProjectOptions"


@dataclass
class DgWorkspaceProjectSpec:
    path: Path
    code_location_name: Optional[str] = None

    @classmethod
    def from_raw(cls, raw: "DgRawWorkspaceProjectSpec") -> Self:
        return cls(
            path=Path(raw["path"]),
            code_location_name=raw.get(
                "code_location_name", DgWorkspaceProjectSpec.code_location_name
            ),
        )


class DgRawWorkspaceProjectSpec(TypedDict, total=False):
    path: Required[str]
    code_location_name: str


@dataclass
class DgWorkspaceScaffoldProjectOptions:
    use_editable_dagster: Union[str, bool] = False

    @classmethod
    def from_raw(cls, raw: "DgRawWorkspaceNewProjectOptions") -> Self:
        return cls(
            use_editable_dagster=raw.get(
                "use_editable_dagster", DgWorkspaceScaffoldProjectOptions.use_editable_dagster
            ),
        )

    # This is here instead of on `DgRawWorkspaceNewProjectOptions` because TypedDict can't have
    # methods.
    @classmethod
    def get_raw_from_cli(
        cls,
        use_editable_dagster: Optional[str],
    ) -> "DgRawWorkspaceNewProjectOptions":
        raw_scaffold_project_options: DgRawWorkspaceNewProjectOptions = {}
        if use_editable_dagster:
            raw_scaffold_project_options["use_editable_dagster"] = (
                True if use_editable_dagster == "TRUE" else use_editable_dagster
            )
        return raw_scaffold_project_options


class DgRawWorkspaceNewProjectOptions(TypedDict, total=False):
    use_editable_dagster: Union[str, bool]


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

# The Dg*FileConfig classes wrap config extracted from a config file. This may be either a dg.toml
# file or a pyproject.toml file. For `dg.toml`, the config is defined a the top level. For
# pyproject.toml the config must be mounted on the `tool.dg` section. Either way, once the config
# has been parsed and extracted into a Dg*FileConfig class, it does not matter which file type it
# was sourced from.

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


def is_dg_specific_config_file(path: Path) -> bool:
    """Check if the file is a dg-specific toml file."""
    return path.name == "dg.toml" or path.name == ".dg.toml"


@contextmanager
def modify_dg_toml_config(path: Path) -> Iterator[Union[tomlkit.TOMLDocument, tomlkit.items.Table]]:
    """Modify a TOML file as a tomlkit.TOMLDocument, preserving comments and formatting."""
    with modify_toml(path) as toml:
        if is_dg_specific_config_file(path):
            yield toml
        elif not has_toml_node(toml, ("tool", "dg")):
            raise KeyError(
                "TOML file does not have a tool.dg section. This is required for pyproject.toml files."
            )
        else:
            yield get_toml_node(toml, ("tool", "dg"), tomlkit.items.Table)


def has_dg_file_config(
    path: Path, predicate: Optional[Callable[[Mapping[str, Any]], bool]] = None
) -> bool:
    toml = load_toml_as_dict(path)
    # `dg.toml` is a special case where settings are defined at the top level
    if is_dg_specific_config_file(path):
        node = toml
    else:
        if "dg" not in toml.get("tool", {}):
            return False
        node = toml["tool"]["dg"]
    return predicate(node) if predicate else True


def load_dg_user_file_config() -> DgRawCliConfig:
    contents = load_config(get_dg_config_path()).get("cli", {})

    return DgRawCliConfig(**{k: v for k, v in contents.items() if k != "plus"})


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
    if is_dg_specific_config_file(path):
        raw_dict = toml.unwrap()
        path_prefix = None
    else:
        raw_dict = get_toml_node(toml, ("tool", "dg"), tomlkit.items.Table).unwrap()
        path_prefix = "tool.dg"
    try:
        config = _DgConfigValidator(path_prefix).validate({k: v for k, v in raw_dict.items()})
    except DgValidationError as e:
        _raise_file_config_validation_error(str(e), path)
    return config


class _DgConfigValidator:
    def __init__(self, path_prefix: Optional[str]) -> None:
        self.path_prefix = path_prefix

    def validate(self, raw_dict: dict[str, Any]) -> DgFileConfig:
        self._validate_file_config_setting(
            raw_dict,
            "directory_type",
            Required[Literal["workspace", "project"]],
        )
        self._validate_dg_config_file_cli_section(raw_dict.get("cli", {}))
        if raw_dict["directory_type"] == "workspace":
            self._validate_file_config_setting(raw_dict, "workspace", dict)
            self._validate_file_config_workspace_section(raw_dict.get("workspace", {}))
            self._validate_file_config_no_extraneous_keys(
                set(DgWorkspaceFileConfig.__annotations__.keys()), raw_dict, None
            )
            return cast(DgWorkspaceFileConfig, raw_dict)
        elif raw_dict["directory_type"] == "project":
            self._validate_file_config_setting(raw_dict, "project", dict)
            self._validate_file_config_project_section(raw_dict.get("project", {}))
            self._validate_file_config_no_extraneous_keys(
                set(DgProjectFileConfig.__annotations__.keys()), raw_dict, None
            )
            return cast(DgProjectFileConfig, raw_dict)
        else:
            raise DgError("Unreachable")

    def _validate_dg_config_file_cli_section(self, section: object) -> None:
        if not isinstance(section, dict):
            self._raise_mistyped_key_error("tool.dg.cli", get_type_str(dict), section)
        for key, type_ in DgRawCliConfig.__annotations__.items():
            self._validate_file_config_setting(section, key, type_, "cli")
        self._validate_file_config_no_extraneous_keys(
            set(DgRawCliConfig.__annotations__.keys()), section, "cli"
        )

    def _validate_file_config_project_section(self, section: object) -> None:
        if not isinstance(section, dict):
            self._raise_mistyped_key_error("project", get_type_str(dict), section)
        for key, type_ in DgRawProjectConfig.__annotations__.items():
            self._validate_file_config_setting(section, key, type_, "project")
        self._validate_file_config_no_extraneous_keys(
            set(DgRawProjectConfig.__annotations__.keys()), section, "project"
        )

    def _validate_file_config_workspace_section(self, section: object) -> None:
        if not isinstance(section, dict):
            self._raise_mistyped_key_error("workspace", get_type_str(dict), section)
        for key, type_ in DgRawWorkspaceConfig.__annotations__.items():
            if key == "projects":
                self._validate_file_config_setting(section, key, list, "workspace")
                for i, spec in enumerate(section.get("projects") or []):
                    self._validate_file_config_workspace_project_spec(spec, i)
            elif key == "scaffold_project_options":
                self._validate_file_config_workspace_scaffold_project_options(
                    section.get("scaffold_project_options", {})
                )
            else:
                self._validate_file_config_setting(section, key, type_, "workspace")
        self._validate_file_config_no_extraneous_keys(
            set(DgRawWorkspaceConfig.__annotations__.keys()), section, "workspace"
        )

    def _validate_file_config_workspace_project_spec(self, section: object, index: int) -> None:
        if not isinstance(section, dict):
            self._raise_mistyped_key_error(
                f"workspace.projects[{index}]", get_type_str(dict), section
            )
        for key, type_ in DgRawWorkspaceProjectSpec.__annotations__.items():
            self._validate_file_config_setting(section, key, type_, f"workspace.projects[{index}]")
        self._validate_file_config_no_extraneous_keys(
            set(DgRawWorkspaceProjectSpec.__annotations__.keys()),
            section,
            f"workspace.projects[{index}]",
        )

    def _validate_file_config_workspace_scaffold_project_options(self, section: object) -> None:
        if not isinstance(section, dict):
            self._raise_mistyped_key_error(
                "workspace.scaffold_project_options", get_type_str(dict), section
            )
        for key, type_ in DgRawWorkspaceNewProjectOptions.__annotations__.items():
            self._validate_file_config_setting(
                section, key, type_, "workspace.scaffold_project_options"
            )
        self._validate_file_config_no_extraneous_keys(
            set(DgRawWorkspaceNewProjectOptions.__annotations__.keys()),
            section,
            "workspace.scaffold_project_options",
        )

    def _validate_file_config_no_extraneous_keys(
        self, valid_keys: set[str], section: Mapping[str, object], toml_path: Optional[str]
    ) -> None:
        extraneous_keys = [k for k in section.keys() if k not in valid_keys]
        if extraneous_keys:
            full_key = self._get_full_key(toml_path)
            raise DgValidationError(f"Unrecognized fields at `{full_key}`: {extraneous_keys}")

    # expected_type Any to handle typing constructs (`Literal` etc)
    def _validate_file_config_setting(
        self,
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
                self._raise_missing_required_key_error(full_key, type_str)
            if error_type == "mistype":
                self._raise_mistyped_key_error(full_key, type_str, section[key])

    def _get_full_key(self, key: Optional[str]) -> str:
        if self.path_prefix:
            return f"{self.path_prefix}.{key}" if key else self.path_prefix
        return key if key else "<root>"

    def _raise_missing_required_key_error(self, key: str, type_str: str) -> Never:
        full_key = self._get_full_key(key)
        raise DgValidationError(f"Missing required value for `{full_key}`. Expected {type_str}.")

    def _raise_mistyped_key_error(self, key: str, type_str: str, value: object) -> Never:
        full_key = self._get_full_key(key)
        raise DgValidationError(
            f"`Invalid value for `{full_key}`. Expected {type_str}, got `{value}`."
        )


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
        arg_strs = sorted([get_type_str(a) for a in args])
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
