import os
from pathlib import Path
from typing import Final, Iterable, Optional, Tuple, Type

import tomli
from dagster._core.errors import DagsterError
from typing_extensions import Self

from dagster_components.core.component import Component, ComponentTypeRegistry

# Code location
_CODE_LOCATION_CUSTOM_COMPONENTS_DIR: Final = "lib"
_CODE_LOCATION_COMPONENT_INSTANCES_DIR: Final = "components"


def is_inside_code_location_project(path: Path) -> bool:
    try:
        find_enclosing_code_location_root_path(path)
        return True
    except DagsterError:
        return False


def find_enclosing_code_location_root_path(path: Path) -> Path:
    """Given a path, locate the code location root directory that contains it. It
    determines this by finding a pyproject.toml with a [tool.dagster] section.

    Searches parent directory recursively until it finds it. It if navigates
    to the root directory, it throws an error.
    """
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
    def from_code_location_path(
        cls,
        path: Path,
        component_registry: "ComponentTypeRegistry",
        components_folder: Optional[Path] = None,
    ) -> Self:
        if not _is_code_location_root(path):
            raise DagsterError(
                f"Path {path} is not a code location root. Must have a pyproject.toml with a [tool.dagster] section."
            )

        name = os.path.basename(path)

        return cls(
            root_path=str(path),
            name=name,
            component_registry=component_registry,
            components_folder=components_folder
            or path / name / _CODE_LOCATION_COMPONENT_INSTANCES_DIR,
        )

    def __init__(
        self,
        root_path: str,
        name: str,
        component_registry: "ComponentTypeRegistry",
        components_folder: Path,
    ):
        self._root_path = root_path
        self._name = name
        self._component_registry = component_registry
        self._components_folder = components_folder

    @property
    def component_types_root_path(self) -> str:
        return os.path.join(self._root_path, self._name, _CODE_LOCATION_CUSTOM_COMPONENTS_DIR)

    @property
    def component_types_root_module(self) -> str:
        return f"{self._name}.{_CODE_LOCATION_CUSTOM_COMPONENTS_DIR}"

    @property
    def component_registry(self) -> "ComponentTypeRegistry":
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
        return str(self._components_folder)

    @property
    def component_instances(self) -> Iterable[str]:
        return sorted(os.listdir(self.component_instances_root_path))

    def has_component_instance(self, name: str) -> bool:
        return os.path.exists(os.path.join(self.component_instances_root_path, name))
