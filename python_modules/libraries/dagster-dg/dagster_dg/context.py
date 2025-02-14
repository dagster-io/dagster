import subprocess
from collections.abc import Iterable
from dataclasses import replace
from functools import cached_property
from pathlib import Path
from typing import Final, Optional

from typing_extensions import Self

from dagster_dg.cache import CachableDataType, DgCache
from dagster_dg.component import RemoteComponentRegistry
from dagster_dg.config import DgConfig, DgPartialConfig, load_dg_config_file
from dagster_dg.error import DgError
from dagster_dg.utils import (
    MISSING_DAGSTER_COMPONENTS_ERROR_MESSAGE,
    NO_LOCAL_VENV_ERROR_MESSAGE,
    NOT_CODE_LOCATION_ERROR_MESSAGE,
    NOT_COMPONENT_LIBRARY_ERROR_MESSAGE,
    NOT_DEPLOYMENT_ERROR_MESSAGE,
    NOT_DEPLOYMENT_OR_CODE_LOCATION_ERROR_MESSAGE,
    ensure_loadable_path,
    exit_with_error,
    generate_missing_dagster_components_in_local_venv_error_message,
    get_path_for_module,
    get_path_for_package,
    get_uv_run_executable_path,
    get_venv_executable,
    is_executable_available,
    is_package_installed,
    pushd,
    resolve_local_venv,
    strip_activated_venv_from_env_vars,
)
from dagster_dg.utils.filesystem import hash_paths

# Deployment
_DEPLOYMENT_CODE_LOCATIONS_DIR: Final = "code_locations"

# Code location
_DEFAULT_CODE_LOCATION_COMPONENTS_LIB_SUBMODULE: Final = "lib"
_DEFAULT_CODE_LOCATION_COMPONENTS_SUBMODULE: Final = "components"


class DgContext:
    root_path: Path
    config: DgConfig
    _cache: Optional[DgCache] = None

    def __init__(self, config: DgConfig, root_path: Path):
        self.config = config
        self.root_path = root_path
        if config.disable_cache or not self.use_dg_managed_environment:
            self._cache = None
        else:
            self._cache = DgCache.from_config(config)
        self.component_registry = RemoteComponentRegistry.empty()

    @classmethod
    def for_deployment_environment(cls, path: Path, cli_config: DgPartialConfig) -> Self:
        context = cls.from_config_file_discovery_and_cli_config(path, cli_config)

        # Commands that operate on a deployment need to be run inside a deployment context.
        if not context.is_deployment:
            exit_with_error(NOT_DEPLOYMENT_ERROR_MESSAGE)
        return context

    @classmethod
    def for_code_location_environment(cls, path: Path, cli_config: DgPartialConfig) -> Self:
        context = cls.from_config_file_discovery_and_cli_config(path, cli_config)

        # Commands that operate on a code location need to be run (a) with dagster-components
        # available; and (b) inside a code location context.
        _validate_dagster_components_availability(context)

        if not context.is_code_location:
            exit_with_error(NOT_CODE_LOCATION_ERROR_MESSAGE)
        return context

    @classmethod
    def for_deployment_or_code_location_environment(
        cls, path: Path, cli_config: DgPartialConfig
    ) -> Self:
        context = cls.from_config_file_discovery_and_cli_config(path, cli_config)

        # Commands that operate on a deployment need to be run inside a deployment or code location
        # context.
        if not (context.is_deployment or context.is_code_location):
            exit_with_error(NOT_DEPLOYMENT_OR_CODE_LOCATION_ERROR_MESSAGE)
        return context

    @classmethod
    def for_component_library_environment(cls, path: Path, cli_config: DgPartialConfig) -> Self:
        context = cls.from_config_file_discovery_and_cli_config(path, cli_config)

        # Commands that operate on a component library need to be run (a) with dagster-components
        # available; (b) in a component library context.
        _validate_dagster_components_availability(context)

        if not context.is_component_library:
            exit_with_error(NOT_COMPONENT_LIBRARY_ERROR_MESSAGE)
        return context

    @classmethod
    def for_defined_registry_environment(cls, path: Path, cli_config: DgPartialConfig) -> Self:
        context = cls.from_config_file_discovery_and_cli_config(path, cli_config)

        # Commands that access the component registry need to be run with dagster-components
        # available.
        _validate_dagster_components_availability(context)
        return context

    @classmethod
    def from_config_file_discovery_and_cli_config(
        cls, path: Path, cli_config: DgPartialConfig
    ) -> Self:
        config_path = DgConfig.discover_config_file(path)
        root_path = config_path.parent if config_path else path
        base_config = DgConfig.from_config_file(config_path) if config_path else DgConfig.default()
        config = replace(base_config, **cli_config)
        return cls(config=config, root_path=root_path)

    @classmethod
    def default(cls) -> Self:
        return cls(DgConfig.default(), Path.cwd())

    # Use to derive a new context for a code location while preserving existing settings
    def with_root_path(self, root_path: Path) -> Self:
        config_path = root_path / "pyproject.toml"
        if not root_path / "pyproject.toml":
            raise DgError(f"Cannot find `pyproject.toml` at {root_path}")
        new_config = replace(self.config, **load_dg_config_file(config_path))
        return self.__class__(config=new_config, root_path=root_path)

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
            *([self.components_lib_path] if self.is_component_library else []),
        ]

    def get_cache_key(self, data_type: CachableDataType) -> tuple[str, str, str]:
        path_parts = [str(part) for part in self.root_path.parts if part != self.root_path.anchor]
        env_hash = hash_paths(self.component_registry_paths())
        return ("_".join(path_parts), env_hash, data_type)

    def get_cache_key_for_local_components(self, path: Path) -> tuple[str, str, str]:
        env_hash = hash_paths([path], includes=["*.py"])
        path_parts = [str(part) for part in path.parts if part != "/"]
        return ("_".join(path_parts), env_hash, "local_component_registry")

    # ########################
    # ##### DEPLOYMENT METHODS
    # ########################

    @property
    def is_deployment(self) -> bool:
        return self.config.is_deployment

    @cached_property
    def deployment_root_path(self) -> Path:
        if not self.is_deployment:
            raise DgError("`deployment_root_path` is only available in a deployment context")
        deployment_config_path = DgConfig.discover_config_file(
            self.root_path, lambda x: x.get("is_deployment", False)
        )
        if not deployment_config_path:
            raise DgError("Cannot find deployment configuration file")
        return deployment_config_path.parent

    def has_code_location(self, name: str) -> bool:
        if not self.is_deployment:
            raise DgError(
                "`deployment_has_code_location` is only available in a deployment context"
            )
        return (self.deployment_root_path / _DEPLOYMENT_CODE_LOCATIONS_DIR / name).is_dir()

    @property
    def code_location_root_path(self) -> Path:
        if not self.is_deployment:
            raise DgError(
                "`deployment_code_location_root_path` is only available in a deployment context"
            )
        return self.deployment_root_path / _DEPLOYMENT_CODE_LOCATIONS_DIR

    def get_code_location_names(self) -> Iterable[str]:
        return [loc.name for loc in sorted(self.code_location_root_path.iterdir())]

    def get_code_location_path(self, name: str) -> Path:
        return self.code_location_root_path / name

    def get_code_location_root_module(self, name: str) -> Path:
        return self.code_location_root_path / name

    # ########################
    # ##### GENERAL PYTHON PACKAGE METHODS
    # ########################

    @property
    def root_package_name(self) -> str:
        return self.config.root_package or self.root_path.name.replace("-", "_")

    # ########################
    # ##### CODE LOCATION METHODS
    # ########################

    @property
    def is_code_location(self) -> bool:
        return self.config.is_code_location

    @property
    def code_location_name(self) -> str:
        if not self.is_code_location:
            raise DgError("`code_location_name` is only available in a code location context")
        return self.root_path.name

    @property
    def code_location_python_executable(self) -> Path:
        if not self.is_code_location:
            raise DgError(
                "`code_location_python_executable` is only available in a code location context"
            )
        return self.root_path / get_venv_executable(Path(".venv"))

    @cached_property
    def components_package_name(self) -> str:
        if not self.is_code_location:
            raise DgError("`components_package_name` is only available in a code location context")
        return (
            self.config.component_package
            or f"{self.root_package_name}.{_DEFAULT_CODE_LOCATION_COMPONENTS_SUBMODULE}"
        )

    @cached_property
    def components_path(self) -> Path:
        if not self.is_code_location:
            raise DgError("`components_path` is only available in a code location context")
        with ensure_loadable_path(self.root_path):
            if not is_package_installed(self.root_package_name):
                raise DgError(
                    f"Could not find expected package `{self.root_package_name}` in the current environment. Components expects the package name to match the directory name of the code location."
                )
            if not is_package_installed(self.components_package_name):
                raise DgError(
                    f"Components package `{self.components_package_name}` is not installed in the current environment."
                )
            return Path(get_path_for_package(self.components_package_name))

    def get_component_instance_names(self) -> Iterable[str]:
        return [str(instance_path.name) for instance_path in self.components_path.iterdir()]

    def has_component_instance(self, name: str) -> bool:
        return (self.components_path / name).is_dir()

    @property
    def definitions_package_name(self) -> str:
        if not self.is_code_location:
            raise DgError("`definitions_package_name` is only available in a code location context")
        return f"{self.root_package_name}.definitions"

    @cached_property
    def definitions_path(self) -> Path:
        with ensure_loadable_path(self.root_path):
            if not is_package_installed(self.definitions_package_name):
                raise DgError(
                    f"Definitions package `{self.definitions_package_name}` is not installed in the current environment."
                )
            return Path(get_path_for_module(self.definitions_package_name))

    # ########################
    # ##### COMPONENT LIBRARY METHODS
    # ########################

    @property
    def is_component_library(self) -> bool:
        return self.config.is_component_lib

    @cached_property
    def components_lib_package_name(self) -> str:
        if not self.is_component_library:
            raise DgError(
                "`components_lib_package_name` is only available in a component library context"
            )
        return (
            self.config.component_lib_package
            or f"{self.root_package_name}.{_DEFAULT_CODE_LOCATION_COMPONENTS_LIB_SUBMODULE}"
        )

    @cached_property
    def components_lib_path(self) -> Path:
        if not self.is_component_library:
            raise DgError("`components_lib_path` is only available in a component library context")
        with ensure_loadable_path(self.root_path):
            if not is_package_installed(self.root_package_name):
                raise DgError(
                    f"Could not find expected package `{self.root_package_name}` in the current environment. Components expects the package name to match the directory name of the code location."
                )
            if not is_package_installed(self.components_lib_package_name):
                raise DgError(
                    f"Components lib package `{self.components_lib_package_name}` is not installed in the current environment."
                )
            return Path(get_path_for_package(self.components_lib_package_name))

    # ########################
    # ##### HELPERS
    # ########################

    def external_components_command(self, command: list[str], log: bool = True) -> str:
        if self.use_dg_managed_environment:
            code_location_command_prefix = ["uv", "run", "dagster-components"]
            env = strip_activated_venv_from_env_vars()
            executable_path = get_uv_run_executable_path("dagster-components")
        else:
            code_location_command_prefix = [self.dagster_components_executable]
            env = strip_activated_venv_from_env_vars()
            executable_path = self.dagster_components_executable
        full_command = [
            *code_location_command_prefix,
            *(
                ["--builtin-component-lib", self.config.builtin_component_lib]
                if self.config.builtin_component_lib
                else []
            ),
            *command,
        ]
        with pushd(self.root_path):
            if log:
                print(f"Using {executable_path}")  # noqa: T201
            result = subprocess.run(full_command, stdout=subprocess.PIPE, env=env, check=True)
            return result.stdout.decode("utf-8")

    def ensure_uv_lock(self, path: Optional[Path] = None) -> None:
        path = path or self.root_path
        with pushd(path):
            if not (path / "uv.lock").exists():
                subprocess.run(["uv", "sync"], check=True, env=strip_activated_venv_from_env_vars())

    @property
    def use_dg_managed_environment(self) -> bool:
        return self.config.use_dg_managed_environment and self.is_code_location

    def validate_deployment_command_environment(self) -> None:
        """Commands that operate on a deployment need to be run inside a deployment context."""
        if not self.is_deployment:
            exit_with_error(NOT_DEPLOYMENT_ERROR_MESSAGE)

    def validate_registry_command_environment(self) -> None:
        """Commands that access the component registry need to be run with dagster-components
        available on $PATH.
        """
        if not is_executable_available("dagster-components"):
            exit_with_error(MISSING_DAGSTER_COMPONENTS_ERROR_MESSAGE)

    @property
    def has_venv(self) -> bool:
        return resolve_local_venv(self.root_path) is not None

    @cached_property
    def venv_path(self) -> Path:
        path = resolve_local_venv(self.root_path)
        if not path:
            raise DgError("Cannot find .venv")
        return path

    @cached_property
    def dagster_components_executable(self) -> Path:
        return get_venv_executable(self.venv_path, "dagster-components")


# ########################
# ##### HELPERS
# ########################


def _validate_dagster_components_availability(context: DgContext) -> None:
    if context.config.require_local_venv:
        if not context.has_venv:
            exit_with_error(NO_LOCAL_VENV_ERROR_MESSAGE)
        elif not context.dagster_components_executable.exists():
            exit_with_error(
                generate_missing_dagster_components_in_local_venv_error_message(
                    str(context.venv_path)
                )
            )
    elif not is_executable_available("dagster-components"):
        exit_with_error(MISSING_DAGSTER_COMPONENTS_ERROR_MESSAGE)
