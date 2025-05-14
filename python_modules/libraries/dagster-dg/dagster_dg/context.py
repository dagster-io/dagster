import datetime
import json
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
import textwrap
from collections.abc import Iterable, Mapping
from functools import cached_property
from pathlib import Path
from typing import Any, Final, Optional, Union

import tomlkit
import tomlkit.items
import yaml
from click.testing import CliRunner
from dagster_shared.libraries import (
    DagsterPyPiAccessError,
    get_published_pypi_versions,
    library_version_from_core_version,
)
from dagster_shared.record import record
from dagster_shared.serdes.serdes import serialize_value, whitelist_for_serdes
from dagster_shared.utils import environ
from packaging.version import Version
from typing_extensions import Self

from dagster_dg.cache import CachableDataType, DgCache
from dagster_dg.component import RemotePluginRegistry
from dagster_dg.config import (
    DgConfig,
    DgProjectPythonEnvironment,
    DgRawBuildConfig,
    DgRawCliConfig,
    DgWorkspaceProjectSpec,
    discover_config_file,
    has_dg_user_file_config,
    load_dg_root_file_config,
    load_dg_user_file_config,
    load_dg_workspace_file_config,
)
from dagster_dg.error import DgError
from dagster_dg.utils import (
    NO_LOCAL_VENV_ERROR_MESSAGE,
    NOT_COMPONENT_LIBRARY_ERROR_MESSAGE,
    NOT_PROJECT_ERROR_MESSAGE,
    NOT_WORKSPACE_ERROR_MESSAGE,
    NOT_WORKSPACE_OR_PROJECT_ERROR_MESSAGE,
    exit_with_error,
    generate_missing_dagster_components_error_message,
    generate_project_and_activated_venv_mismatch_warning,
    generate_tool_dg_cli_in_project_in_workspace_error_message,
    get_activated_venv,
    get_logger,
    get_toml_node,
    get_venv_executable,
    has_toml_node,
    msg_with_potential_paths,
    pushd,
    resolve_local_venv,
    strip_activated_venv_from_env_vars,
)
from dagster_dg.utils.filesystem import hash_paths
from dagster_dg.utils.version import get_uv_tool_core_pin_string
from dagster_dg.utils.warnings import emit_warning
from dagster_dg.version import __version__

# Project
_DEFAULT_PROJECT_DEFS_SUBMODULE: Final = "defs"
_DEFAULT_PROJECT_CODE_LOCATION_TARGET_MODULE: Final = "definitions"
_EXCLUDED_COMPONENT_DIRECTORIES: Final = {"__pycache__"}


def _should_capture_components_cli_stderr() -> bool:
    """Used in tests to pass along stderr from the components CLI to the parent process."""
    return False


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
        self._cache = None if config.cli.disable_cache else DgCache.from_config(config)
        self.component_registry = RemotePluginRegistry.empty()

        # Always run this check, its a no-op if there is no pyproject.toml.
        _validate_plugin_entry_point(self)

    @classmethod
    def for_workspace_environment(cls, path: Path, command_line_config: DgRawCliConfig) -> Self:
        context = cls.from_file_discovery_and_command_line_config(path, command_line_config)

        # Commands that operate on a workspace need to be run inside a workspace context.
        if not context.is_workspace:
            potential_paths = cls._locate_potential_projects_or_workspaces(
                path, command_line_config, allow_projects=False, allow_workspaces=True
            )
            if potential_paths:
                exit_with_error(
                    msg_with_potential_paths(NOT_WORKSPACE_ERROR_MESSAGE, potential_paths)
                )
            exit_with_error(NOT_WORKSPACE_ERROR_MESSAGE)
        return context

    @classmethod
    def for_project_environment(cls, path: Path, command_line_config: DgRawCliConfig) -> Self:
        context = cls.from_file_discovery_and_command_line_config(path, command_line_config)

        if not context.is_project:
            potential_paths = cls._locate_potential_projects_or_workspaces(
                path, command_line_config, allow_projects=True, allow_workspaces=False
            )
            if potential_paths:
                exit_with_error(
                    msg_with_potential_paths(NOT_PROJECT_ERROR_MESSAGE, potential_paths)
                )
            exit_with_error(NOT_PROJECT_ERROR_MESSAGE)
        _validate_project_venv_activated(context)
        return context

    @classmethod
    def _locate_potential_projects_or_workspaces(
        cls,
        path: Path,
        command_line_config: DgRawCliConfig,
        allow_projects: bool,
        allow_workspaces: bool,
    ) -> list[Path]:
        """Locates potential project or workspace directories by iterating over parent directories
        or immediate children, to present to the user if they run a command in a directory that
        is not a project or workspace.
        """
        potential_paths = [
            *path.parents,
            *path.iterdir(),
        ]
        matching_paths = []
        for path in potential_paths:
            context = cls.from_file_discovery_and_command_line_config(path, command_line_config)
            if context.is_workspace and allow_workspaces:
                matching_paths.append(path)
            elif context.is_project and allow_projects:
                matching_paths.append(path)
        return matching_paths

    @classmethod
    def for_workspace_or_project_environment(
        cls, path: Path, commmand_line_config: DgRawCliConfig
    ) -> Self:
        context = cls.from_file_discovery_and_command_line_config(path, commmand_line_config)

        # Commands that operate on a workspace need to be run inside a workspace or project
        # context.
        if not (context.is_workspace or context.is_project):
            potential_paths = cls._locate_potential_projects_or_workspaces(
                path, commmand_line_config, allow_projects=True, allow_workspaces=True
            )
            if potential_paths:
                exit_with_error(
                    msg_with_potential_paths(
                        NOT_WORKSPACE_OR_PROJECT_ERROR_MESSAGE, potential_paths
                    )
                )
            exit_with_error(NOT_WORKSPACE_OR_PROJECT_ERROR_MESSAGE)
        if context.is_project:
            _validate_project_venv_activated(context)
        return context

    @classmethod
    def for_component_library_environment(
        cls, path: Path, command_line_config: DgRawCliConfig
    ) -> Self:
        context = cls.from_file_discovery_and_command_line_config(path, command_line_config)

        # Commands that operate on a component library need to be run (a) with dagster-components
        # available; (b) in a component library context.
        _validate_dagster_components_availability(context)

        if not context.is_plugin:
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

        cli_config_warning = None
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
                    # We have to emit this _after_ we merge all configs to ensure we have the right
                    # suppression list.
                    cli_config_warning = generate_tool_dg_cli_in_project_in_workspace_error_message(
                        root_path, workspace_root_path
                    )
        else:
            root_path = Path.cwd()
            workspace_root_path = None
            root_file_config = None
            container_workspace_file_config = None

        user_config = load_dg_user_file_config() if has_dg_user_file_config() else None
        config = DgConfig.from_partial_configs(
            root_file_config=root_file_config,
            container_workspace_file_config=container_workspace_file_config,
            command_line_config=command_line_config,
            user_config=user_config,
        )
        if cli_config_warning:
            emit_warning(
                "cli_config_in_workspace_project", cli_config_warning, config.cli.suppress_warnings
            )

        context = cls(
            config=config,
            root_path=root_path,
            workspace_root_path=workspace_root_path,
            cli_opts=command_line_config,
        )
        _validate_dg_up_to_date(context)

        return context

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

    @property
    def is_plugin_cache_enabled(self) -> bool:
        return self.has_cache and self.has_uv_lock

    def component_registry_paths(self) -> list[Path]:
        """Paths that should be watched for changes to the component registry."""
        return [
            self.root_path / "uv.lock",
            *([self.default_plugin_module_path] if self.is_plugin else []),
        ]

    # Allowing open-ended str data_type for now so we can do module names
    def get_cache_key(self, data_type: Union[CachableDataType, str]) -> tuple[str, str, str]:
        path_parts = [str(part) for part in self.root_path.parts if part != self.root_path.anchor]
        paths_to_hash = [
            self.root_path / "uv.lock",
            *([self.default_plugin_module_path] if self.is_plugin else []),
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

    def get_cache_key_for_update_check_timestamp(self) -> tuple[str]:
        return ("dg_update_check_timestamp",)

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
        elif self.is_plugin:
            return self.default_plugin_module_name.split(".")[0]
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
        if self.has_uv_lock:
            return ["uv", "pip"]

        executable = self.get_executable("python")
        has_pip = (
            subprocess.run(
                [str(executable), "-m", "pip"],
                check=False,
                capture_output=True,
            ).returncode
            == 0
        )
        return [str(executable), "-m", "pip"] if has_pip else ["uv", "pip"]

    @property
    def should_run_dagster_in_process(self) -> bool:
        """If the current python environment where dg is running is the same as the target environment
        and we should attempt to run dagster subcommands directly in process.
        """
        if self.use_dg_managed_environment:
            return False

        if os.getenv("DG_DISABLE_IN_PROCESS"):
            return False

        # resolve to jump any symlinks for "python3" etc that can exist in venv
        return Path(sys.executable).resolve() == self.get_executable("python").resolve()

    @cached_property
    def dagster_version(self) -> Version:
        if self.should_run_dagster_in_process:
            from dagster.version import __version__ as dagster_version

            return Version(dagster_version)

        return self._get_module_version("dagster")

    def _get_module_version(self, module_name: str) -> Version:
        with pushd(self.root_path):
            args = [
                "list",
                "--format",
                "json",
            ]
            python_args = ["--python", str(self._resolve_executable("python"))]
            executable_args = self.resolve_package_manager_executable()
            if executable_args[0] == "uv":
                all_args = [*executable_args, *args, *python_args]
            else:
                all_args = [*executable_args, *python_args, *args]

            result = subprocess.check_output(
                all_args,
                env=strip_activated_venv_from_env_vars(os.environ),
            )
        modules = json.loads(result)
        for module in modules:
            if module["name"] == module_name:
                return Version(module["version"])
        raise DgError(f"Module `{module_name}` not found")

    @property
    def project_python_executable(self) -> Path:
        if not self.is_project:
            raise DgError(
                "`project_python_executable` is only available in a Dagster project context"
            )
        return self.root_path / get_venv_executable(Path(".venv"))

    @cached_property
    def build_config_path(self) -> Path:
        return self.root_path / "build.yaml"

    @cached_property
    def build_config(self) -> Optional[DgRawBuildConfig]:
        build_yaml_path = self.build_config_path

        if not build_yaml_path.resolve().exists():
            return None

        with open(build_yaml_path) as f:
            build_config_dict = yaml.safe_load(f)
            build_directory = build_config_dict.get("directory")
            if build_directory:
                build_directory_path = Path(build_directory)
                if not build_directory_path.is_absolute():
                    build_directory_path = (build_yaml_path.parent / build_directory_path).resolve()
                build_config_dict["directory"] = str(build_directory_path.resolve())

            return build_config_dict

    @cached_property
    def container_context_config_path(self) -> Path:
        return self.root_path / "container_context.yaml"

    @cached_property
    def container_context_config(self) -> Optional[Mapping[str, Any]]:
        container_context_yaml_path = self.container_context_config_path

        if not container_context_yaml_path.resolve().exists():
            return None

        with open(container_context_yaml_path) as f:
            return yaml.safe_load(f)

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
    # ##### PLUGIN METHODS
    # ########################

    # It is possible for a single package to define multiple entry points under the
    # `dagster_dg.plugin` entry point group. At present, `dg` only cares about the first one, which
    # it uses for all component type scaffolding operations.

    @property
    def is_plugin(self) -> bool:
        return bool(self._dagster_components_entry_points)

    @cached_property
    def default_plugin_module_name(self) -> str:
        if not self._dagster_components_entry_points:
            raise DgError(
                "`default_component_library_module_name` is only available in a component library context"
            )
        return next(iter(self._dagster_components_entry_points.values()))

    @cached_property
    def default_plugin_module_path(self) -> Path:
        if not self.is_plugin:
            raise DgError(
                "`default_plugin_module_path` is only available in a component library context"
            )
        return self.get_path_for_local_module(self.default_plugin_module_name)

    @cached_property
    def _dagster_components_entry_points(self) -> Mapping[str, str]:
        if self.pyproject_toml_path.exists():
            toml = tomlkit.parse(self.pyproject_toml_path.read_text())
            if has_toml_node(toml, ("project", "entry-points", "dagster_dg.plugin")):
                return get_toml_node(
                    toml,
                    ("project", "entry-points", "dagster_dg.plugin"),
                    (tomlkit.items.Table, tomlkit.items.InlineTable),
                ).unwrap()
            # Keeping for a few weeks (as of 2025-04-09) for backwards compatibility. Should be removed
            # eventually.
            elif has_toml_node(toml, ("project", "entry-points", "dagster_dg.library")):
                return get_toml_node(
                    toml,
                    ("project", "entry-points", "dagster_dg.library"),
                    (tomlkit.items.Table, tomlkit.items.InlineTable),
                ).unwrap()
        if self.setup_cfg_path.exists():
            import warnings

            from setuptools import SetuptoolsDeprecationWarning
            from setuptools.config import read_configuration

            # Ignore deprecation warnings for the read_configuration function
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=SetuptoolsDeprecationWarning)
                config = read_configuration("setup.cfg")
            entry_points = config.get("options", {}).get("entry_points", {})
            if "dagster_dg.plugin" in entry_points:
                raw_plugin_entry_points = entry_points["dagster_dg.plugin"]
            elif "dagster_dg.library" in entry_points:
                raw_plugin_entry_points = entry_points["dagster_dg.library"]
            else:
                raw_plugin_entry_points = []
            plugin_entry_points = {}
            for entry_point in raw_plugin_entry_points:
                k, v = re.split(r"\s*=\s*", entry_point, 1)
                plugin_entry_points[k] = v
            return plugin_entry_points
        return {}

    # ########################
    # ##### LOG METHODS
    # ########################

    @cached_property
    def log(self) -> logging.Logger:
        """Return a logger for this context.

        The logger is configured based on the verbose setting in config.
        Default level is WARNING, and if verbose is set, level is increased to INFO.

        Returns:
            A configured logger that can be used with methods like info(), debug(), warning(), etc.
        """
        return get_logger("dagster_dg.context", self.config.cli.verbose)

    # ########################
    # ##### HELPERS
    # ########################

    def external_dagster_cloud_cli_command(
        self, command: list[str], log: bool = True, env: Optional[dict[str, str]] = None
    ):
        command = [
            "uv",
            "tool",
            "run",
            "--from",
            f"dagster-cloud-cli{get_uv_tool_core_pin_string()}",
            "dagster-cloud",
            *command,
        ]
        with pushd(self.root_path):
            result = subprocess.run(command, check=False, env={**os.environ, **(env or {})})
            if result.returncode != 0:
                exit_with_error(f"""
                    An error occurred while executing a `dagster-cloud` command via `uv tool run`.

                    `{shlex.join(command)}` exited with code {result.returncode}. Aborting.
                """)

    def external_components_command(
        self,
        command: list[str],
        log: bool = True,
        additional_env: Optional[Mapping[str, str]] = None,
    ) -> str:
        if self.should_run_dagster_in_process and self.is_project:
            # targeting our current environment
            from dagster.components.cli import cli

            with environ(additional_env or {}):
                result = CliRunner().invoke(
                    cli,
                    command,
                    catch_exceptions=False,
                )

            return result.stdout

        _validate_dagster_dg_and_dagster_version_compatibility(self)
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
                self.log.warning(f"Using {executable_path}")

            # We don't capture stderr here-- it will print directly to the console, then we can
            # add a clean error message at the end explaining what happened.
            should_capture_stderr = _should_capture_components_cli_stderr()
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE if should_capture_stderr else None,
                env=env,
                check=False,
            )
            if result.returncode != 0:
                exit_with_error(f"""
                    An error occurred while executing a `dagster-components` command in the {self.environment_desc}.

                    `{shlex.join(command)}` exited with code {result.returncode}. Aborting.{result.stderr.decode("utf-8") if should_capture_stderr else ""}
                """)
            else:
                return result.stdout.decode("utf-8")

    @property
    def has_uv_lock(self) -> bool:
        """Check if the uv.lock file exists in the root path."""
        return (self.root_path / "uv.lock").exists()

    def ensure_uv_lock(self, path: Optional[Path] = None) -> None:
        path = path or self.root_path
        if not (path / "uv.lock").exists():
            self.ensure_uv_sync(path)

    def ensure_uv_sync(self, path: Optional[Path] = None) -> None:
        path = path or self.root_path
        with pushd(path):
            if not (path / "uv.lock").exists():
                subprocess.check_output(
                    ["uv", "sync"],
                    env=strip_activated_venv_from_env_vars(os.environ),
                )

    @property
    def use_dg_managed_environment(self) -> bool:
        return bool(self.config.project and self.config.project.python_environment.uv_managed)

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

    @property
    def setup_cfg_path(self) -> Path:
        return self.root_path / "setup.cfg"

    def get_path_for_local_module(self, module_name: str) -> Path:
        if not self.is_project and not self.is_plugin:
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
        exit_with_error(f"Cannot find module `{module_name}` in the current project.")


# ########################
# ##### HELPERS
# ########################


def _validate_dagster_components_availability(context: DgContext) -> None:
    if context.use_dg_managed_environment:
        if not context.has_venv:
            exit_with_error(NO_LOCAL_VENV_ERROR_MESSAGE)
        elif not get_venv_executable(context.venv_path, "dagster-components").exists():
            exit_with_error(
                generate_missing_dagster_components_error_message(str(context.venv_path))
            )
    elif not context.has_executable("dagster-components"):
        exit_with_error(generate_missing_dagster_components_error_message())


def _validate_project_venv_activated(context: DgContext) -> None:
    if not context.config.project:
        raise DgError(
            "`_validate_project_venv_activated` is only available in a Dagster project context"
        )
    activated_venv = get_activated_venv()
    project_venv = context.root_path / ".venv"
    if (
        context.config.project.python_environment.active
        and project_venv.exists()
        and project_venv != activated_venv
    ):
        msg = generate_project_and_activated_venv_mismatch_warning(project_venv, activated_venv)
        emit_warning(
            "project_and_activated_venv_mismatch",
            msg,
            context.config.cli.suppress_warnings,
        )


# Can be removed when we drop support for dagster_dg.library
def _validate_plugin_entry_point(context: DgContext) -> None:
    if not context.pyproject_toml_path.exists():
        return
    toml = tomlkit.parse(context.pyproject_toml_path.read_text())
    if has_toml_node(toml, ("project", "entry-points", "dagster_dg.library")):
        emit_warning(
            "deprecated_dagster_dg_library_entry_point",
            f"""
            Found deprecated `dagster_dg.library` entry point group in:
                {context.pyproject_toml_path}

            Please update the group name to `dagster_dg.plugin`. Package reinstallation is required
            because entry points are registered at install time. Reinstall your package to your
            environment using:

                [uv]  $ uv pip install -e .
                [pip] $ pip install -e .

            """,
            context.config.cli.suppress_warnings,
        )


DG_UPDATE_CHECK_INTERVAL = datetime.timedelta(hours=1)
DG_UPDATE_CHECK_ENABLED_ENV_VAR = "DAGSTER_DG_UPDATE_CHECK_ENABLED"


@whitelist_for_serdes
@record
class DgPyPiVersionInfo:
    timestamp: float
    raw_versions: list[str]

    @property
    def datetime(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self.timestamp)

    @cached_property
    def versions(self) -> list[Version]:
        return sorted(Version(v) for v in self.raw_versions)


def _validate_dg_up_to_date(context: DgContext) -> None:
    # Don't check if we've disabled the check
    if not (
        bool(int(os.getenv(DG_UPDATE_CHECK_ENABLED_ENV_VAR, "1")))
        and "dg_outdated" not in context.config.cli.suppress_warnings
    ):
        return

    version_info = _get_dg_pypi_version_info(context)
    if version_info is None:  # Nothing cached and network error occurred
        return None

    installed_version = Version(__version__)
    latest_version = version_info.versions[-1]
    if installed_version < latest_version:
        emit_warning(
            "dg_outdated",
            f"""
            There is a new version of `dagster-dg` available:

                Latest version: {latest_version}
                Installed version: {installed_version}

            Update your dagster-dg installation to keep up to date:

                [uv tool]  $ uv tool upgrade dagster-dg
                [uv local] $ uv sync --upgrade dagster-dg
                [pip]      $ pip install --upgrade dagster-dg
            """,
            context.config.cli.suppress_warnings,
        )


def _get_dg_pypi_version_info(context: DgContext) -> Optional[DgPyPiVersionInfo]:
    key = context.get_cache_key_for_update_check_timestamp()
    if context.has_cache:
        version_info = context.cache.get(key, DgPyPiVersionInfo)
    else:
        version_info = None

    now = datetime.datetime.now()
    if version_info and now - version_info.datetime < DG_UPDATE_CHECK_INTERVAL:
        return version_info
    else:
        try:
            if context.config.cli.verbose:
                context.log.info("Checking for the latest version of `dagster-dg` on PyPI.")
            published_versions = get_published_pypi_versions("dagster-dg")
            version_info = DgPyPiVersionInfo(
                raw_versions=[str(v) for v in published_versions], timestamp=now.timestamp()
            )
            if context.has_cache:
                context.cache.set(key, serialize_value(version_info))
        except DagsterPyPiAccessError as e:
            emit_warning(
                "dg_outdated",
                f"""
                There was an error checking for the latest version of `dagster-dg` on PyPI. Please check your
                internet connection and try again.

                Error: {e}
                """,
                context.config.cli.suppress_warnings,
            )
    return version_info


def _validate_dagster_dg_and_dagster_version_compatibility(context: DgContext) -> None:
    dagster_dg_version = Version(__version__)
    dagster_version = context.dagster_version
    minimum_dagster_dg_version = Version(library_version_from_core_version(str(dagster_version)))
    if dagster_dg_version < minimum_dagster_dg_version:
        exit_with_error(
            textwrap.dedent(f"""
            Current `dg` version ({dagster_dg_version}) is incompatible with `dagster` version ({dagster_version}) in the resolved environment.
            Please upgrade your `dg` version to at least {minimum_dagster_dg_version} in order to use `dg` with this environment.

                dg version: {dagster_dg_version}
                dg executable: {shutil.which("dg")}

                dagster version: {dagster_version}
                dagster executable: {context.get_executable("dagster")}
            """).strip(),
            do_format=False,
        )
