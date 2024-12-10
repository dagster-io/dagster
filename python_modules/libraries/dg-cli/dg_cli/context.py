import json
import os
from pathlib import Path
from typing import Final, Iterable, Mapping, Optional, Sequence

import tomli
from typing_extensions import Self

from dg_cli.component import RemoteComponentRegistry, RemoteComponentType
from dg_cli.error import DgError
from dg_cli.utils import execute_code_location_command


def is_inside_deployment_project(path: Path) -> bool:
    try:
        _resolve_deployment_root_path(path)
        return True
    except DgError:
        return False


def _resolve_deployment_root_path(path: Path) -> Path:
    current_path = path.absolute()
    while not _is_deployment_root(current_path):
        current_path = current_path.parent
        if str(current_path) == "/":
            raise DgError("Cannot find deployment root")
    return current_path


def is_inside_code_location_project(path: Path) -> bool:
    try:
        _resolve_code_location_root_path(path)
        return True
    except DgError:
        return False


def _resolve_code_location_root_path(path: Path) -> Path:
    current_path = path.absolute()
    while not _is_code_location_root(current_path):
        current_path = current_path.parent
        if str(current_path) == "/":
            raise DgError("Cannot find code location root")
    return current_path


def _is_deployment_root(path: Path) -> bool:
    return (path / "code_locations").exists()


def _is_code_location_root(path: Path) -> bool:
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


class DeploymentProjectContext:
    @classmethod
    def from_path(cls, path: Path) -> Self:
        return cls(root_path=_resolve_deployment_root_path(path))

    def __init__(self, root_path: Path):
        self._root_path = root_path

    @property
    def deployment_root(self) -> Path:
        return self._root_path

    @property
    def code_location_root_path(self) -> Path:
        return self._root_path / _DEPLOYMENT_CODE_LOCATIONS_DIR

    def has_code_location(self, name: str) -> bool:
        return os.path.exists(os.path.join(self._root_path, "code_locations", name))

    def list_code_locations(self) -> Iterable[str]:
        return sorted(os.listdir(os.path.join(self._root_path, "code_locations")))


class CodeLocationProjectContext:
    _components_registry: Mapping[str, RemoteComponentType] = {}

    @classmethod
    def from_path(cls, path: Path) -> Self:
        root_path = _resolve_code_location_root_path(path)
        raw_component_registry = execute_code_location_command(
            root_path, ["list", "component-types"]
        )
        component_registry = RemoteComponentRegistry.from_dict(json.loads(raw_component_registry))
        deployment_context = (
            DeploymentProjectContext.from_path(path) if is_inside_deployment_project(path) else None
        )

        return cls(
            deployment_context=deployment_context,
            root_path=root_path,
            name=path.name,
            component_registry=component_registry,
        )

    def __init__(
        self,
        deployment_context: Optional[DeploymentProjectContext],
        root_path: Path,
        name: str,
        component_registry: "RemoteComponentRegistry",
    ):
        self._deployment_context = deployment_context
        self._root_path = root_path
        self._name = name
        self._component_registry = component_registry

    @property
    def name(self) -> str:
        return self._name

    @property
    def deployment_context(self) -> Optional[DeploymentProjectContext]:
        return self._deployment_context

    @property
    def component_types_root_path(self) -> str:
        return os.path.join(self._root_path, self._name, _CODE_LOCATION_CUSTOM_COMPONENTS_DIR)

    @property
    def component_types_root_module(self) -> str:
        return f"{self._name}.{_CODE_LOCATION_CUSTOM_COMPONENTS_DIR}"

    @property
    def component_registry(self) -> "RemoteComponentRegistry":
        return self._component_registry

    def has_component_type(self, name: str) -> bool:
        return self._component_registry.has(name)

    def get_component_type(self, name: str) -> RemoteComponentType:
        if not self.has_component_type(name):
            raise DgError(f"No component type named {name}")
        return self._component_registry.get(name)

    def list_component_types(self) -> Sequence[str]:
        return sorted(self._component_registry.keys())

    def get_component_instance_path(self, name: str) -> str:
        if name not in self.component_instances:
            raise DgError(f"No component instance named {name}")
        return os.path.join(self.component_instances_root_path, name)

    @property
    def component_instances_root_path(self) -> str:
        return os.path.join(self._root_path, self._name, _CODE_LOCATION_COMPONENT_INSTANCES_DIR)

    @property
    def component_instances(self) -> Iterable[str]:
        return os.listdir(
            os.path.join(self._root_path, self._name, _CODE_LOCATION_COMPONENT_INSTANCES_DIR)
        )

    def has_component_instance(self, name: str) -> bool:
        return os.path.exists(
            os.path.join(self._root_path, self._name, _CODE_LOCATION_COMPONENT_INSTANCES_DIR, name)
        )
