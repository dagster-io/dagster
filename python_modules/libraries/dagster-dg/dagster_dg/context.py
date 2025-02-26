import shlex
import shutil
import subprocess
from collections.abc import Iterable, Mapping
from functools import cached_property
from pathlib import Path
from typing import Final, Optional

import tomlkit
import tomlkit.items
from typing_extensions import Self

from dagster_dg.cache import CachableDataType, DgCache, hash_paths
from dagster_dg.component import RemoteComponentRegistry
from dagster_dg.config import (
    DgConfig,
    DgRawCliConfig,
    discover_config_file,
    load_dg_root_file_config,
    load_dg_workspace_file_config,
)
from dagster_dg.error import DgError
from dagster_dg.utils import (
    MISSING_DAGSTER_COMPONENTS_ERROR_MESSAGE,
    NO_LOCAL_VENV_ERROR_MESSAGE,
    NOT_COMPONENT_LIBRARY_ERROR_MESSAGE,
    NOT_PROJECT_ERROR_MESSAGE,
    NOT_WORKSPACE_ERROR_MESSAGE,
    NOT_WORKSPACE_OR_PROJECT_ERROR_MESSAGE,
    ensure_loadable_path,
    exit_with_error,
    generate_missing_dagster_components_in_local_venv_error_message,
    get_path_for_module,
    get_toml_value,
    get_venv_executable,
    has_toml_value,
    is_package_installed,
    pushd,
    resolve_local_venv,
    strip_activated_venv_from_env_vars,
)

# Project
_DEFAULT_PROJECT_COMPONENTS_LIB_SUBMODULE: Final = "lib"
_DEFAULT_PROJECT_COMPONENTS_SUBMODULE: Final = "components"

# Workspace
_WORKSPACE_PROJECTS_DIR: Final = "projects"


class DgContext:
    root_path: Path
    workspace_root_path: Optional[Path]
    config: DgConfig
    cli_opts: Optional[DgRawCliConfig] = None
    _cache: Optional[DgCache] = None

    # We need to preserve CLI options for the context to be able to derive new contexts, because
    # cli_options override everything else. If we didn't maintain them we wouldn't be able to tell
    # whether a given config option should be overridden in a new derived context.
    def __init__(
        self,
        config: DgConfig,
        root_path: Path,
        workspace_root_path: Optional[Path] = None,
        cli_opts: Optional[DgRawCliConfig] = None,
    ):
        self.config = config
        self.root_path = root_path
        self.workspace_root_path = workspace_root_path
        self.cli_opts = cli_opts
        if config.cli.disable_cache or not self.use_dg_managed_environment:
            self._cache = None
        else:
            self._cache = DgCache.from_config(config)
        self.component_registry = RemoteComponentRegistry.empty()

    @classmethod
    def for_workspace_environment(cls, path: Path, command_line_config: DgRawCliConfig) -> Self:
        context = cls.from_file_discovery_and_command_line_config(path, command_line_config)

        # Commands that operate on a workspace need to be run inside a workspace context.
        if not context.is_workspace:
            exit_with_error(NOT_WORKSPACE_ERROR_MESSAGE)
        return context

    @classmethod
    def for_project_environment(cls, path: Path, command_line_config: DgRawCliConfig) -> Self:
        context = cls.from_file_discovery_and_command_line_config(path, command_line_config)

        # Commands that operate on a project need to be run (a) with dagster-components
        # available; and (b) inside a Dagster project context.
        _validate_dagster_components_availability(context)

        if not context.is_project:
            exit_with_error(NOT_PROJECT_ERROR_MESSAGE)
        return context

    @classmethod
    def for_workspace_or_project_environment(
        cls, path: Path, commmand_line_config: DgRawCliConfig
    ) -> Self:
        context = cls.from_file_discovery_and_command_line_config(path, commmand_line_config)

        # Commands that operate on a workspace need to be run inside a workspace or project
        # context.
        if not (context.is_workspace or context.is_project):
            exit_with_error(NOT_WORKSPACE_OR_PROJECT_ERROR_MESSAGE)
        return context

    @classmethod
    def for_component_library_environment(
        cls, path: Path, command_line_config: DgRawCliConfig
    ) -> Self:
        context = cls.from_file_discovery_and_command_line_config(path, command_line_config)

        # Commands that operate on a component library need to be run (a) with dagster-components
        # available; (b) in a component library context.
        _validate_dagster_components_availability(context)

        if not context.is_component_library:
            exit_with_error(NOT_COMPONENT_LIBRARY_ERROR_MESSAGE)
        return context

    @classmethod
    def for_defined_registry_environment(
        cls, path: Path, command_line_config: DgRawCliConfig
    ) -> Self:
        context = cls.from_file_discovery_and_command_line_config(path, command_line_config)

        # Commands that access the component registry need to be run with dagster-components
        # available.
        _validate_dagster_components_availability(context)
        return context

    @classmethod
    def from_file_discovery_and_command_line_config(
        cls,
        path: Path,
        command_line_config: DgRawCliConfig,
    ) -> Self:
        config_path = discover_config_file(path)
        workspace_config_path = discover_config_file(
            path, lambda x: bool(x.get("directory_type") == "workspace")
        )

        if config_path:
            root_path = config_path.parent
            root_file_config = load_dg_root_file_config(config_path)
            if workspace_config_path:
                workspace_root_path = workspace_config_path.parent

                # If the workspace config is different from the root config, we need to load the
                # workspace config.
                container_workspace_file_config = (
                    load_dg_workspace_file_config(workspace_config_path)
                    if config_path != workspace_config_path
                    else None
                )

            else:
                container_workspace_file_config = None
                workspace_root_path = None
        else:
            root_path = Path.cwd()
            workspace_root_path = None
            root_file_config = None
            container_workspace_file_config = None
        config = DgConfig.from_partial_configs(
            root_file_config=root_file_config,
            container_workspace_file_config=container_workspace_file_config,
            command_line_config=command_line_config,
        )

        return cls(
            config=config,
            root_path=root_path,
            workspace_root_path=workspace_root_path,
            cli_opts=command_line_config,
        )

    @classmethod
    def default(cls) -> Self:
        return cls(DgConfig.default(), Path.cwd())

    # Use to derive a new context for a project while preserving existing settings
    def with_root_path(self, root_path: Path) -> Self:
        if not root_path / "pyproject.toml":
            raise DgError(f"Cannot find `pyproject.toml` at {root_path}")
        return self.__class__.from_file_discovery_and_command_line_config(
            root_path, self.cli_opts or {}
        )

    # ########################
    # ##### CACHE METHODS
    # ########################

    @property
    def cache(self) -> DgCache:
        if not self._cache:
            raise DgError("Cache is disabled")
        return self._cache

    @property
    def has_cache(self) -> bool:
        return self._cache is not None

    def get_cache_key(self, data_type: CachableDataType) -> tuple[str, str, str]:
        path_parts = [str(part) for part in self.root_path.parts if part != self.root_path.anchor]
        paths_to_hash = [
            self.root_path / "uv.lock",
            *([self.default_components_library_path] if self.is_component_library else []),
        ]
        env_hash = hash_paths(paths_to_hash)
        return ("_".join(path_parts), env_hash, data_type)

    def get_cache_key_for_module(self, module_name: str) -> tuple[str, str, str]:
        path = self.get_path_for_module(module_name)
        env_hash = hash_paths([path], includes=["*.py"])
        path_parts = [str(part) for part in path.parts if part != "/"]
        return ("_".join(path_parts), env_hash, "local_component_registry")

    # ########################
    # ##### WORKSPACE METHODS
    # ########################

    @property
    def is_workspace(self) -> bool:
        return self.workspace_root_path is not None

    def get_workspace_project_path(self, name: str) -> Path:
        if not self.workspace_root_path:
            raise DgError("`get_workspace_project_path` is only available in a workspace context")
        return self.workspace_root_path / _WORKSPACE_PROJECTS_DIR / name

    def has_project(self, name: str) -> bool:
        if not self.is_workspace:
            raise DgError("`has_project` is only available in a workspace context")

        return self.get_workspace_project_path(name).is_dir()

    @property
    def project_root_path(self) -> Path:
        if not self.workspace_root_path:
            raise DgError("`project_root_path` is only available in a workspace context")
        return self.workspace_root_path / _WORKSPACE_PROJECTS_DIR

    def get_project_names(self) -> Iterable[str]:
        return [loc.name for loc in sorted(self.project_root_path.iterdir())]

    def get_project_path(self, name: str) -> Path:
        return self.project_root_path / name

    def get_project_root_module(self, name: str) -> Path:
        return self.project_root_path / name

    # ########################
    # ##### GENERAL PYTHON PACKAGE METHODS
    # ########################

    @property
    def root_module_name(self) -> str:
        if self.config.project:
            return self.config.project.root_module
        elif self.is_component_library:
            return self.default_components_library_module.split(".")[0]
        else:
            raise DgError("Cannot determine root package name")

    # ########################
    # ##### PROJECT METHODS
    # ########################

    @property
    def is_project(self) -> bool:
        return self.config.project is not None

    @property
    def project_name(self) -> str:
        if not self.is_project:
            raise DgError("`project_name` is only available in a Dagster project context")
        return self.root_path.name

    @property
    def project_python_executable(self) -> Path:
        if not self.is_project:
            raise DgError(
                "`project_python_executable` is only available in a Dagster project context"
            )
        return self.root_path / get_venv_executable(Path(".venv"))

    @cached_property
    def components_module_name(self) -> str:
        if not self.config.project:
            raise DgError("`components_module_name` is only available in a Dagster project context")
        return (
            self.config.project.components_module
            or f"{self.root_module_name}.{_DEFAULT_PROJECT_COMPONENTS_SUBMODULE}"
        )

    @cached_property
    def components_path(self) -> Path:
        if not self.is_project:
            raise DgError("`components_path` is only available in a Dagster project context")
        return self.get_path_for_module(self.components_module_name)

    def get_component_instance_names(self) -> Iterable[str]:
        return [str(instance_path.name) for instance_path in self.components_path.iterdir()]

    def get_component_instance_module(self, name: str) -> str:
        return f"{self.components_module_name}.{name}"

    def has_component_instance(self, name: str) -> bool:
        return (self.components_path / name).is_dir()

    @property
    def definitions_module_name(self) -> str:
        if not self.is_project:
            raise DgError(
                "`definitions_module_name` is only available in a Dagster project context"
            )
        return f"{self.root_module_name}.definitions"

    @cached_property
    def definitions_path(self) -> Path:
        return self.get_path_for_module(self.definitions_module_name)

    # ########################
    # ##### COMPONENT LIBRARY METHODS
    # ########################

    # It is possible for a single package to define multiple entry points under the
    # `dagster.components` entry point group. At present, `dg` only cares about the first one, which
    # it uses for all component type scaffolding operations.

    @property
    def is_component_library(self) -> bool:
        return bool(self._dagster_components_entry_points)

    @cached_property
    def default_components_library_module(self) -> str:
        if not self._dagster_components_entry_points:
            raise DgError(
                "`default_components_library_module_name` is only available in a component library context"
            )
        return next(iter(self._dagster_components_entry_points.values()))

    @cached_property
    def default_components_library_path(self) -> Path:
        if not self.is_component_library:
            raise DgError("`components_lib_path` is only available in a component library context")
        return self.get_path_for_module(self.default_components_library_module)

    @cached_property
    def _dagster_components_entry_points(self) -> Mapping[str, str]:
        if not self.pyproject_toml_path.exists():
            return {}
        toml = tomlkit.parse(self.pyproject_toml_path.read_text())
        if not has_toml_value(toml, ("project", "entry-points", "dagster.components")):
            return {}
        else:
            return get_toml_value(
                toml,
                ("project", "entry-points", "dagster.components"),
                (tomlkit.items.Table, tomlkit.items.InlineTable),
            ).unwrap()

    # ########################
    # ##### HELPERS
    # ########################

    def external_components_command(self, command: list[str], log: bool = True) -> str:
        executable_path = self.get_executable("dagster-components")
        if self.use_dg_managed_environment:
            # uv run will resolve to the same dagster-components as we resolve above
            project_command_prefix = ["uv", "run", "dagster-components"]
            env = strip_activated_venv_from_env_vars()
        else:
            project_command_prefix = [str(executable_path)]
            env = None
        full_command = [
            *project_command_prefix,
            *(
                ["--builtin-component-lib", self.config.cli.builtin_component_lib]
                if self.config.cli.builtin_component_lib
                else []
            ),
            *command,
        ]
        with pushd(self.root_path):
            if log:
                print(f"Using {executable_path}")  # noqa: T201

            # We don't capture stderr here-- it will print directly to the console, then we can
            # add a clean error message at the end explanining what happened.
            result = subprocess.run(full_command, stdout=subprocess.PIPE, env=env, check=False)
            if result.returncode != 0:
                exit_with_error(f"""
                    An error occurred while executing a `dagster-components` command in the {self.environment_desc}.

                    `{shlex.join(full_command)}` exited with code {result.returncode}. Aborting.
                """)
            else:
                return result.stdout.decode("utf-8")

    def ensure_uv_lock(self, path: Optional[Path] = None) -> None:
        path = path or self.root_path
        with pushd(path):
            if not (path / "uv.lock").exists():
                subprocess.run(["uv", "sync"], check=True, env=strip_activated_venv_from_env_vars())

    @property
    def use_dg_managed_environment(self) -> bool:
        return self.config.cli.use_dg_managed_environment and self.is_project

    @property
    def has_venv(self) -> bool:
        return resolve_local_venv(self.root_path) is not None

    @cached_property
    def venv_path(self) -> Path:
        path = resolve_local_venv(self.root_path)
        if not path:
            raise DgError("Cannot find .venv")
        return path

    def has_executable(self, command: str) -> bool:
        return self._resolve_executable(command) is not None

    def get_executable(self, command: str) -> Path:
        if not (executable := self._resolve_executable(command)):
            raise DgError(f"Cannot find executable {command}")
        return executable

    def _resolve_executable(self, command: str) -> Optional[Path]:
        if (
            self.has_venv
            and (venv_exec := get_venv_executable(self.venv_path, command))
            and venv_exec.exists()
        ):
            return venv_exec
        elif not self.use_dg_managed_environment and (global_exec := shutil.which(command)):
            return Path(global_exec)
        else:
            return None

    @property
    def environment_desc(self) -> str:
        if self.has_venv:
            return f"Python environment at {self.venv_path}"
        else:
            return "ambient Python environment"

    @property
    def pyproject_toml_path(self) -> Path:
        return self.root_path / "pyproject.toml"

    def get_path_for_module(self, module_name: str) -> Path:
        with ensure_loadable_path(self.root_path):
            parts = module_name.split(".")
            for i in range(len(parts)):
                leading_module_name = ".".join(parts[: i + 1])
                if not is_package_installed(leading_module_name):
                    raise DgError(
                        f"Module `{leading_module_name}` is not installed in the current environment."
                    )
            return Path(get_path_for_module(module_name))


# ########################
# ##### HELPERS
# ########################


def _validate_dagster_components_availability(context: DgContext) -> None:
    if context.config.cli.require_local_venv:
        if not context.has_venv:
            exit_with_error(NO_LOCAL_VENV_ERROR_MESSAGE)
        elif not get_venv_executable(context.venv_path, "dagster-components").exists():
            exit_with_error(
                generate_missing_dagster_components_in_local_venv_error_message(
                    str(context.venv_path)
                )
            )
    elif not context.has_executable("dagster-components"):
        exit_with_error(MISSING_DAGSTER_COMPONENTS_ERROR_MESSAGE)
