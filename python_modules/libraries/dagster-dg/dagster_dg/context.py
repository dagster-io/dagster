import json
import os
from pathlib import Path
from typing import Final, Iterable, Mapping, Optional

import tomli
from typing_extensions import Self

from dagster_dg.component import RemoteComponentRegistry, RemoteComponentType
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


class DeploymentDirectoryContext:
    @classmethod
    def from_path(cls, path: Path) -> Self:
        return cls(root_path=_resolve_deployment_root_directory(path))

    def __init__(self, root_path: Path):
        self._root_path = root_path

    @property
    def root_path(self) -> Path:
        return self._root_path

    @property
    def code_location_root_path(self) -> Path:
        return self._root_path / _DEPLOYMENT_CODE_LOCATIONS_DIR

    def has_code_location(self, name: str) -> bool:
        return (self._root_path / "code_locations" / name).is_dir()

    def get_code_location_names(self) -> Iterable[str]:
        return [loc.name for loc in sorted((self._root_path / "code_locations").iterdir())]


class CodeLocationDirectoryContext:
    _components_registry: Mapping[str, RemoteComponentType] = {}

    @classmethod
    def from_path(cls, path: Path) -> Self:
        root_path = _resolve_code_location_root_directory(path)
        component_registry_data = execute_code_location_command(
            root_path, ["list", "component-types"]
        )
        component_registry = RemoteComponentRegistry.from_dict(json.loads(component_registry_data))

        return cls(
            root_path=root_path,
            name=path.name,
            component_registry=component_registry,
            deployment_context=DeploymentDirectoryContext.from_path(path)
            if is_inside_deployment_directory(path)
            else None,
        )

    def __init__(
        self,
        root_path: Path,
        name: str,
        component_registry: "RemoteComponentRegistry",
        deployment_context: Optional[DeploymentDirectoryContext],
    ):
        self._deployment_context = deployment_context
        self._root_path = root_path
        self._name = name
        self._component_registry = component_registry

    @property
    def name(self) -> str:
        return self._name

    @property
    def deployment_context(self) -> Optional[DeploymentDirectoryContext]:
        return self._deployment_context

    @property
    def component_registry(self) -> "RemoteComponentRegistry":
        return self._component_registry

    @property
    def local_component_types_root_path(self) -> str:
        return os.path.join(self._root_path, self._name, _CODE_LOCATION_CUSTOM_COMPONENTS_DIR)

    @property
    def local_component_types_root_module_name(self) -> str:
        return f"{self._name}.{_CODE_LOCATION_CUSTOM_COMPONENTS_DIR}"

    def get_component_type_names(self) -> Iterable[str]:
        return sorted(self._component_registry.keys())

    def has_component_type(self, name: str) -> bool:
        return self._component_registry.has(name)

    def get_component_type(self, name: str) -> RemoteComponentType:
        if not self.has_component_type(name):
            raise DgError(f"No component type named {name}")
        return self._component_registry.get(name)

    @property
    def component_instances_root_path(self) -> Path:
        return self._root_path / self._name / _CODE_LOCATION_COMPONENT_INSTANCES_DIR

    @property
    def component_instances_root_module_name(self) -> str:
        return f"{self._name}.{_CODE_LOCATION_COMPONENT_INSTANCES_DIR}"

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
