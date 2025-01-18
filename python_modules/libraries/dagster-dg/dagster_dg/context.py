import subprocess
from collections.abc import Iterable
from dataclasses import replace
from functools import cached_property
from pathlib import Path
from typing import Final, Optional

from typing_extensions import Self

from dagster_dg.cache import CachableDataType, DgCache, hash_paths
from dagster_dg.component import RemoteComponentRegistry
from dagster_dg.config import DgConfig, DgPartialConfig, load_dg_config_file
from dagster_dg.error import DgError
from dagster_dg.utils import (
    ensure_loadable_path,
    get_path_for_package,
    get_uv_command_env,
    is_package_installed,
    pushd,
)

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
        # self.use_dg_managed_environment is a property derived from self.config
        if config.disable_cache or not self.use_dg_managed_environment:
            self._cache = None
        else:
            self._cache = DgCache.from_config(config)
        self.component_registry = RemoteComponentRegistry.empty()

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

    def get_cache_key(self, data_type: CachableDataType) -> tuple[str, str, str]:
        path_parts = [str(part) for part in self.root_path.parts if part != "/"]
        paths_to_hash = [
            self.root_path / "uv.lock",
            *([self.components_lib_path] if self.is_component_library else []),
        ]
        env_hash = hash_paths(paths_to_hash)
        return ("_".join(path_parts), env_hash, data_type)

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
            if not is_package_installed(self.components_package_name):
                raise DgError(
                    f"Components package `{self.components_package_name}` is not installed in the current environment."
                )
            return Path(get_path_for_package(self.components_package_name))

    def get_component_names(self) -> Iterable[str]:
        return [str(instance_path.name) for instance_path in self.components_path.iterdir()]

    def has_component(self, name: str) -> bool:
        return (self.components_path / name).is_dir()

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
            if not is_package_installed(self.components_lib_package_name):
                raise DgError(
                    f"Components lib package `{self.components_lib_package_name}` is not installed in the current environment."
                )
            return Path(get_path_for_package(self.components_lib_package_name))

    # ########################
    # ##### HELPERS
    # ########################

    def external_components_command(self, command: list[str]) -> str:
        if self.use_dg_managed_environment:
            code_location_command_prefix = ["uv", "run", "dagster-components"]
            env = get_uv_command_env()
        else:
            code_location_command_prefix = ["dagster-components"]
            env = None
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
            result = subprocess.run(full_command, stdout=subprocess.PIPE, env=env, check=True)
            return result.stdout.decode("utf-8")

    def ensure_uv_lock(self, path: Optional[Path] = None) -> None:
        path = path or self.root_path
        with pushd(path):
            if not (path / "uv.lock").exists():
                subprocess.run(["uv", "sync"], check=True, env=get_uv_command_env())

    @property
    def use_dg_managed_environment(self) -> bool:
        return self.config.use_dg_managed_environment and self.is_code_location
