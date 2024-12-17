import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Iterable, Optional, Tuple

import click
import tomli
from typing_extensions import Self

from dagster_dg.component import RemoteComponentRegistry, RemoteComponentType
from dagster_dg.config import DgConfig
from dagster_dg.error import DgError
from dagster_dg.utils import execute_code_location_command


def is_inside_deployment_directory(path: Path) -> bool:
    try:
        _resolve_deployment_root_directory(path)
        return True
    except DgError:
        return False


def _resolve_deployment_root_directory(path: Path) -> Path:
    current_path = path.absolute()
    while not _is_deployment_root_directory(current_path):
        current_path = current_path.parent
        if str(current_path) == "/":
            raise DgError("Cannot find deployment root")
    return current_path


def _is_deployment_root_directory(path: Path) -> bool:
    return (path / "code_locations").exists()


def is_inside_code_location_directory(path: Path) -> bool:
    try:
        _resolve_code_location_root_directory(path)
        return True
    except DgError:
        return False


def _resolve_code_location_root_directory(path: Path) -> Path:
    current_path = path.absolute()
    while not _is_code_location_root_directory(current_path):
        current_path = current_path.parent
        if str(current_path) == "/":
            raise DgError("Cannot find code location root")
    return current_path


def _is_code_location_root_directory(path: Path) -> bool:
    if (path / "pyproject.toml").exists():
        with open(path / "pyproject.toml") as f:
            toml = tomli.loads(f.read())
            return bool(toml.get("tool", {}).get("dagster"))
    return False


# Deployment
_DEPLOYMENT_CODE_LOCATIONS_DIR: Final = "code_locations"

# Code location
_CODE_LOCATION_CUSTOM_COMPONENTS_DIR: Final = "lib"
_CODE_LOCATION_COMPONENT_INSTANCES_DIR: Final = "components"


@dataclass
class DgContext:
    config: DgConfig

    @classmethod
    def from_cli_context(cls, cli_context: click.Context) -> Self:
        return cls.from_config(config=DgConfig.from_cli_context(cli_context))

    @classmethod
    def from_config(cls, config: DgConfig) -> Self:
        return cls(config=config)

    @classmethod
    def default(cls) -> Self:
        return cls.from_config(DgConfig.default())


@dataclass
class DeploymentDirectoryContext:
    root_path: Path
    dg_context: DgContext

    @classmethod
    def from_path(cls, path: Path, dg_context: DgContext) -> Self:
        return cls(root_path=_resolve_deployment_root_directory(path), dg_context=dg_context)

    @property
    def code_location_root_path(self) -> Path:
        return self.root_path / _DEPLOYMENT_CODE_LOCATIONS_DIR

    def has_code_location(self, name: str) -> bool:
        return (self.root_path / "code_locations" / name).is_dir()

    def get_code_location_names(self) -> Iterable[str]:
        return [loc.name for loc in sorted((self.root_path / "code_locations").iterdir())]


@dataclass
class CodeLocationDirectoryContext:
    """Class encapsulating contextual information about a components code location directory.

    Args:
        root_path (Path): The absolute path to the root of the code location directory.
        name (str): The name of the code location python package.
        component_registry (ComponentRegistry): The component registry for the code location.
        deployment_context (Optional[DeploymentDirectoryContext]): The deployment context containing
            the code location directory. Defaults to None.
        dg_context (DgContext): The global application context.
    """

    root_path: Path
    name: str
    component_registry: "RemoteComponentRegistry"
    deployment_context: Optional[DeploymentDirectoryContext]
    dg_context: DgContext

    @classmethod
    def from_path(cls, path: Path, dg_context: DgContext) -> Self:
        root_path = _resolve_code_location_root_directory(path)
        component_registry_data = execute_code_location_command(
            root_path, ["list", "component-types"], dg_context
        )
        component_registry = RemoteComponentRegistry.from_dict(json.loads(component_registry_data))

        return cls(
            root_path=root_path,
            name=path.name,
            component_registry=component_registry,
            deployment_context=DeploymentDirectoryContext.from_path(path, dg_context)
            if is_inside_deployment_directory(path)
            else None,
            dg_context=dg_context,
        )

    @property
    def config(self) -> DgConfig:
        return self.dg_context.config

    @property
    def local_component_types_root_path(self) -> str:
        return os.path.join(self.root_path, self.name, _CODE_LOCATION_CUSTOM_COMPONENTS_DIR)

    @property
    def local_component_types_root_module_name(self) -> str:
        return f"{self.name}.{_CODE_LOCATION_CUSTOM_COMPONENTS_DIR}"

    def iter_component_types(self) -> Iterable[Tuple[str, RemoteComponentType]]:
        for key in sorted(self.component_registry.keys()):
            yield key, self.component_registry.get(key)

    def has_component_type(self, name: str) -> bool:
        return self.component_registry.has(name)

    def get_component_type(self, name: str) -> RemoteComponentType:
        if not self.has_component_type(name):
            raise DgError(f"No component type named {name}")
        return self.component_registry.get(name)

    @property
    def component_instances_root_path(self) -> Path:
        return self.root_path / self.name / _CODE_LOCATION_COMPONENT_INSTANCES_DIR

    @property
    def component_instances_root_module_name(self) -> str:
        return f"{self.name}.{_CODE_LOCATION_COMPONENT_INSTANCES_DIR}"

    def get_component_instance_names(self) -> Iterable[str]:
        return [
            str(instance_path.name)
            for instance_path in self.component_instances_root_path.iterdir()
        ]

    def get_component_instance_path(self, name: str) -> Path:
        if not self.has_component_instance(name):
            raise DgError(f"No component instance named {name}")
        return self.component_instances_root_path / name

    def has_component_instance(self, name: str) -> bool:
        return (self.component_instances_root_path / name).is_dir()
