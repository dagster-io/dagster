import os
from pathlib import Path
from typing import Final, Iterable, Tuple, Type

import tomli
from dagster._core.errors import DagsterError
from typing_extensions import Self

from dagster_components.core.component import Component, ComponentRegistry

# Code location
_CODE_LOCATION_CUSTOM_COMPONENTS_DIR: Final = "lib"
_CODE_LOCATION_COMPONENT_INSTANCES_DIR: Final = "components"


def is_inside_code_location_project(path: Path) -> bool:
    try:
        _resolve_code_location_root_path(path)
        return True
    except DagsterError:
        return False


def _resolve_code_location_root_path(path: Path) -> Path:
    current_path = path.absolute()
    while not _is_code_location_root(current_path):
        current_path = current_path.parent
        if str(current_path) == "/":
            raise DagsterError("Cannot find code location root")
    return current_path


def _is_code_location_root(path: Path) -> bool:
    if (path / "pyproject.toml").exists():
        with open(path / "pyproject.toml") as f:
            toml = tomli.loads(f.read())
            return bool(toml.get("tool", {}).get("dagster"))
    return False


class CodeLocationProjectContext:
    @classmethod
    def from_path(cls, path: Path, component_registry: "ComponentRegistry") -> Self:
        root_path = _resolve_code_location_root_path(path)
        return cls(
            root_path=str(root_path),
            name=os.path.basename(root_path),
            component_registry=component_registry,
        )

    def __init__(
        self,
        root_path: str,
        name: str,
        component_registry: "ComponentRegistry",
    ):
        self._root_path = root_path
        self._name = name
        self._component_registry = component_registry

    @property
    def component_types_root_path(self) -> str:
        return os.path.join(self._root_path, self._name, _CODE_LOCATION_CUSTOM_COMPONENTS_DIR)

    @property
    def component_types_root_module(self) -> str:
        return f"{self._name}.{_CODE_LOCATION_CUSTOM_COMPONENTS_DIR}"

    @property
    def component_registry(self) -> "ComponentRegistry":
        return self._component_registry

    def has_component_type(self, name: str) -> bool:
        return self._component_registry.has(name)

    def get_component_type(self, name: str) -> Type[Component]:
        if not self.has_component_type(name):
            raise DagsterError(f"No component type named {name}")
        return self._component_registry.get(name)

    def list_component_types(self) -> Iterable[Tuple[str, Type[Component]]]:
        for key in sorted(self._component_registry.keys()):
            yield key, self._component_registry.get(key)

    def get_component_instance_path(self, name: str) -> str:
        if name not in self.component_instances:
            raise DagsterError(f"No component instance named {name}")
        return os.path.join(self.component_instances_root_path, name)

    @property
    def component_instances_root_path(self) -> str:
        return os.path.join(self._root_path, self._name, _CODE_LOCATION_COMPONENT_INSTANCES_DIR)

    @property
    def component_instances(self) -> Iterable[str]:
        return sorted(
            os.listdir(
                os.path.join(self._root_path, self._name, _CODE_LOCATION_COMPONENT_INSTANCES_DIR)
            )
        )

    def has_component_instance(self, name: str) -> bool:
        return os.path.exists(
            os.path.join(self._root_path, self._name, _CODE_LOCATION_COMPONENT_INSTANCES_DIR, name)
        )
