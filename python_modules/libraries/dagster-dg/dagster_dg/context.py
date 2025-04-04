import json
import os
import shlex
import shutil
import subprocess
import warnings
from collections.abc import Iterable, Mapping
from functools import cached_property
from pathlib import Path
from typing import Final, Optional, Union

import tomlkit
import tomlkit.items
from dagster_shared.utils.config import does_dg_config_file_exist
from typing_extensions import Self

from dagster_dg.cache import CachableDataType, DgCache
from dagster_dg.component import RemoteLibraryObjectRegistry
from dagster_dg.config import (
    DgConfig,
    DgProjectPythonEnvironment,
    DgRawCliConfig,
    DgWorkspaceProjectSpec,
    discover_config_file,
    load_dg_root_file_config,
    load_dg_user_file_config,
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
    exit_with_error,
    generate_missing_dagster_components_in_local_venv_error_message,
    generate_tool_dg_cli_in_project_in_workspace_error_message,
    get_toml_node,
    get_venv_executable,
    has_toml_node,
    pushd,
    resolve_local_venv,
    strip_activated_venv_from_env_vars,
)
from dagster_dg.utils.filesystem import hash_paths

# Project
_DEFAULT_PROJECT_DEFS_SUBMODULE: Final = "defs"
_DEFAULT_PROJECT_CODE_LOCATION_TARGET_MODULE: Final = "definitions"
_EXCLUDED_COMPONENT_DIRECTORIES: Final = {"__pycache__"}


class DgContext:
    root_path: Path
    config: DgConfig
    cli_opts: Optional[DgRawCliConfig] = None
    _cache: Optional[DgCache] = None
    _workspace_root_path: Optional[Path]

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
        self._workspace_root_path = workspace_root_path
        self.cli_opts = cli_opts
        if config.cli.disable_cache or not self.use_dg_managed_environment:
            self._cache = None
        else:
            self._cache = DgCache.from_config(config)
        self.component_registry = RemoteLibraryObjectRegistry.empty()

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
        root_config_path = discover_config_file(path)
        workspace_config_path = discover_config_file(
            path, lambda x: bool(x.get("directory_type") == "workspace")
        )

        if root_config_path:
            root_path = root_config_path.parent
            root_file_config = load_dg_root_file_config(root_config_path)
            if workspace_config_path is None:
                workspace_root_path = None
                container_workspace_file_config = None

            # Only load the workspace config if the workspace root is different from the first
            # detected root.
            elif workspace_config_path == root_config_path:
                workspace_root_path = workspace_config_path.parent
                container_workspace_file_config = None
            else:
                workspace_root_path = workspace_config_path.parent
                container_workspace_file_config = load_dg_workspace_file_config(
                    workspace_config_path
                )
                if "cli" in root_file_config:
                    del root_file_config["cli"]
                    warnings.warn(
                        generate_tool_dg_cli_in_project_in_workspace_error_message(
                            root_path, workspace_root_path
                        )
                    )
        else:
            root_path = Path.cwd()
            workspace_root_path = None
            root_file_config = None
            container_workspace_file_config = None

        user_config = load_dg_user_file_config() if does_dg_config_file_exist() else None
        config = DgConfig.from_partial_configs(
            root_file_config=root_file_config,
            container_workspace_file_config=container_workspace_file_config,
            command_line_config=command_line_config,
            user_config=user_config,
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
        if not ((root_path / "pyproject.toml").exists() or (root_path / "dg.toml").exists()):
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

    def component_registry_paths(self) -> list[Path]:
        """Paths that should be watched for changes to the component registry."""
        return [
            self.root_path / "uv.lock",
            *([self.default_component_library_path] if self.is_component_library else []),
        ]

    # Allowing open-ended str data_type for now so we can do module names
    def get_cache_key(self, data_type: Union[CachableDataType, str]) -> tuple[str, str, str]:
        path_parts = [str(part) for part in self.root_path.parts if part != self.root_path.anchor]
        paths_to_hash = [
            self.root_path / "uv.lock",
            *([self.default_component_library_path] if self.is_component_library else []),
        ]
        env_hash = hash_paths(paths_to_hash)
        return ("_".join(path_parts), env_hash, data_type)

    def get_cache_key_for_module(self, module_name: str) -> tuple[str, str, str]:
        if module_name.startswith(self.root_module_name):
            path = self.get_path_for_local_module(module_name)
            env_hash = hash_paths([path], includes=["*.py"])
            path_parts = [str(part) for part in path.parts if part != "/"]
            return ("_".join(path_parts), env_hash, "local_component_registry")
        else:
            return self.get_cache_key(module_name)

    # ########################
    # ##### WORKSPACE METHODS
    # ########################

    @property
    def is_workspace(self) -> bool:
        return self._workspace_root_path is not None

    @property
    def workspace_root_path(self) -> Path:
        if not self._workspace_root_path:
            raise DgError("`workspace_root_path` is only available in a workspace context")
        return self._workspace_root_path

    def has_project(self, relative_path: Path) -> bool:
        if not self.is_workspace:
            raise DgError("`has_project` is only available in a workspace context")
        return bool(
            next(
                (spec for spec in self.project_specs if spec.path == relative_path),
                None,
            )
        )

    @property
    def project_specs(self) -> list[DgWorkspaceProjectSpec]:
        if not self.config.workspace:
            raise DgError("`project_specs` is only available in a workspace context")
        return self.config.workspace.projects

    # ########################
    # ##### GENERAL PYTHON PACKAGE METHODS
    # ########################

    @property
    def root_module_name(self) -> str:
        if self.config.project:
            return self.config.project.root_module
        elif self.is_component_library:
            return self.default_component_library_module_name.split(".")[0]
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

    def resolve_package_manager_executable(self) -> list[str]:
        if self.use_dg_managed_environment:
            return ["uv", "pip"]
        else:
            return [str(self.get_executable("python")), "-m", "pip"]

    def get_module_version(self, module_name: str) -> str:
        if not self.use_dg_managed_environment:
            raise DgError("`get_module_version` is only available in a Dagster project context")

        with pushd(self.root_path):
            result = subprocess.check_output(
                [
                    *self.resolve_package_manager_executable(),
                    "list",
                    "--format",
                    "json",
                    "--python",
                    get_venv_executable(Path(".venv")),
                ],
                env=strip_activated_venv_from_env_vars(os.environ),
            )
        modules = json.loads(result)
        for module in modules:
            if module["name"] == module_name:
                return module["version"]
        raise DgError(f"Module `{module_name}` not found")

    @property
    def project_python_executable(self) -> Path:
        if not self.is_project:
            raise DgError(
                "`project_python_executable` is only available in a Dagster project context"
            )
        return self.root_path / get_venv_executable(Path(".venv"))

    @cached_property
    def defs_module_name(self) -> str:
        if not self.config.project:
            raise DgError("`defs_module_name` is only available in a Dagster project context")
        return (
            self.config.project.defs_module
            or f"{self.root_module_name}.{_DEFAULT_PROJECT_DEFS_SUBMODULE}"
        )

    @cached_property
    def defs_path(self) -> Path:
        if not self.is_project:
            raise DgError("`defs_path` is only available in a Dagster project context")
        return self.get_path_for_local_module(self.defs_module_name)

    def get_component_instance_names(self) -> Iterable[str]:
        return [
            str(p.name)
            for p in self.defs_path.iterdir()
            if p.is_dir() and str(p.name) not in _EXCLUDED_COMPONENT_DIRECTORIES
        ]

    def get_component_instance_module_name(self, name: str) -> str:
        return f"{self.defs_module_name}.{name}"

    def has_component_instance(self, name: str) -> bool:
        return (self.defs_path / name).is_dir()

    @property
    def code_location_target_module_name(self) -> str:
        if not self.config.project:
            raise DgError(
                "`code_location_target_module_name` is only available in a Dagster project context"
            )
        return (
            self.config.project.code_location_target_module
            or f"{self.root_module_name}.{_DEFAULT_PROJECT_CODE_LOCATION_TARGET_MODULE}"
        )

    @cached_property
    def code_location_target_path(self) -> Path:
        return self.get_path_for_local_module(self.code_location_target_module_name)

    @property
    def code_location_name(self) -> str:
        if not self.config.project:
            raise DgError("`code_location_name` is only available in a Dagster project context")
        return self.config.project.code_location_name or self.project_name

    @property
    def python_environment(self) -> DgProjectPythonEnvironment:
        if not self.config.project:
            raise DgError("`python_environment` is only available in a Dagster project context")
        return self.config.project.python_environment

    # ########################
    # ##### COMPONENT LIBRARY METHODS
    # ########################

    # It is possible for a single package to define multiple entry points under the
    # `dagster_dg.library` entry point group. At present, `dg` only cares about the first one, which
    # it uses for all component type scaffolding operations.

    @property
    def is_component_library(self) -> bool:
        return bool(self._dagster_components_entry_points)

    @cached_property
    def default_component_library_module_name(self) -> str:
        if not self._dagster_components_entry_points:
            raise DgError(
                "`default_component_library_module_name` is only available in a component library context"
            )
        return next(iter(self._dagster_components_entry_points.values()))

    @cached_property
    def default_component_library_path(self) -> Path:
        if not self.is_component_library:
            raise DgError(
                "`default_component_library_path` is only available in a component library context"
            )
        return self.get_path_for_local_module(self.default_component_library_module_name)

    @cached_property
    def _dagster_components_entry_points(self) -> Mapping[str, str]:
        if not self.pyproject_toml_path.exists():
            return {}
        toml = tomlkit.parse(self.pyproject_toml_path.read_text())
        if not has_toml_node(toml, ("project", "entry-points", "dagster_dg.library")):
            return {}
        else:
            return get_toml_node(
                toml,
                ("project", "entry-points", "dagster_dg.library"),
                (tomlkit.items.Table, tomlkit.items.InlineTable),
            ).unwrap()

    # ########################
    # ##### HELPERS
    # ########################

    def external_components_command(
        self,
        command: list[str],
        log: bool = True,
        additional_env: Optional[Mapping[str, str]] = None,
    ) -> str:
        executable_path = self.get_executable("dagster-components")
        if self.use_dg_managed_environment:
            # uv run will resolve to the same dagster-components as we resolve above
            command = ["uv", "run", "dagster-components", *command]
            env = strip_activated_venv_from_env_vars(os.environ)
        else:
            command = [str(executable_path), *command]
            env = os.environ

        if additional_env:
            env = {**env, **additional_env}

        with pushd(self.root_path):
            if log:
                print(f"Using {executable_path}")  # noqa: T201

            # We don't capture stderr here-- it will print directly to the console, then we can
            # add a clean error message at the end explanining what happened.
            result = subprocess.run(command, stdout=subprocess.PIPE, env=env, check=False)
            if result.returncode != 0:
                exit_with_error(f"""
                    An error occurred while executing a `dagster-components` command in the {self.environment_desc}.

                    `{shlex.join(command)}` exited with code {result.returncode}. Aborting.
                """)
            else:
                return result.stdout.decode("utf-8")

    def ensure_uv_lock(self, path: Optional[Path] = None) -> None:
        path = path or self.root_path
        with pushd(path):
            if not (path / "uv.lock").exists():
                subprocess.run(
                    ["uv", "sync"], check=True, env=strip_activated_venv_from_env_vars(os.environ)
                )

    @property
    def use_dg_managed_environment(self) -> bool:
        return bool(
            self.config.project and self.config.project.python_environment == "persistent_uv"
        )

    @property
    def has_venv(self) -> bool:
        return self.use_dg_managed_environment and (resolve_local_venv(self.root_path) is not None)

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
            return "active Python environment"

    @property
    def config_file_path(self) -> Path:
        return self.dg_toml_path if self.dg_toml_path.exists() else self.pyproject_toml_path

    @property
    def dg_toml_path(self) -> Path:
        return self.root_path / "dg.toml"

    @property
    def pyproject_toml_path(self) -> Path:
        return self.root_path / "pyproject.toml"

    def get_path_for_local_module(self, module_name: str) -> Path:
        if not self.is_project and not self.is_component_library:
            raise DgError(
                "`get_path_for_local_module` is only available in a project or component library context"
            )
        if not module_name.startswith(self.root_module_name):
            raise DgError(f"Module `{module_name}` is not part of the current project.")

        # Attempt to resolve the path for a local module by looking in both `src` and the root
        # level. Unfortunately there is no setting reliably present in pyproject.toml or setup.py
        # that can be relied on to know in advance the package root (src or root level).
        for path in [
            self.root_path / "src" / Path(*module_name.split(".")),
            self.root_path / Path(*module_name.split(".")),
        ]:
            if path.exists():
                return path
            elif path.with_suffix(".py").exists():
                return path.with_suffix(".py")
        raise DgError(f"Cannot find module `{module_name}` in the current project.")


# ########################
# ##### HELPERS
# ########################


def _validate_dagster_components_availability(context: DgContext) -> None:
    if context.use_dg_managed_environment:
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
