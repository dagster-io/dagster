import os
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Optional

import tomli
from dagster._core.errors import DagsterError
from typing_extensions import Self

from dagster_components.core.component import Component, ComponentTypeRegistry
from dagster_components.utils import ensure_loadable_path, get_path_for_package

# Code location
_DEFAULT_CODE_LOCATION_COMPONENTS_LIB_SUBMODULE: Final = "lib"
_DEFAULT_CODE_LOCATION_COMPONENTS_SUBMODULE: Final = "components"


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


@dataclass
class CodeLocationConfig:
    component_package: Optional[str] = None


def _load_code_location_config(path: Path) -> CodeLocationConfig:
    with open(path / "pyproject.toml") as f:
        toml = tomli.loads(f.read())
        raw_dg_config = toml.get("tool", {}).get("dg", {})
        raw_config = {
            k: v for k, v in raw_dg_config.items() if k in CodeLocationConfig.__annotations__
        }
        return CodeLocationConfig(**raw_config)


class CodeLocationProjectContext:
    @classmethod
    def from_code_location_path(
        cls,
        path: Path,
        component_registry: "ComponentTypeRegistry",
        components_path: Optional[Path] = None,
        components_package_name: Optional[str] = None,
    ) -> Self:
        if not _is_code_location_root(path):
            raise DagsterError(
                f"Path {path} is not a code location root. Must have a pyproject.toml with a [tool.dagster] section."
            )

        name = os.path.basename(path)
        config = _load_code_location_config(path)
        components_package_name = (
            config.component_package or f"{name}.{_DEFAULT_CODE_LOCATION_COMPONENTS_SUBMODULE}"
        )
        if not components_path:
            with ensure_loadable_path(path):
                components_path = (
                    Path(get_path_for_package(config.component_package))
                    if config.component_package
                    else path / name / _DEFAULT_CODE_LOCATION_COMPONENTS_SUBMODULE
                )

        return cls(
            root_path=str(path),
            name=name,
            component_registry=component_registry,
            components_path=components_path,
            components_package_name=components_package_name,
        )

    def __init__(
        self,
        root_path: str,
        name: str,
        component_registry: "ComponentTypeRegistry",
        components_path: Path,
        components_package_name: str,
    ):
        self._root_path = root_path
        self._name = name
        self._component_registry = component_registry
        self._components_path = components_path
        self._components_package_name = components_package_name

    @property
    def component_registry(self) -> "ComponentTypeRegistry":
        return self._component_registry

    def has_component_type(self, name: str) -> bool:
        return self._component_registry.has(name)

    def get_component_type(self, name: str) -> type[Component]:
        if not self.has_component_type(name):
            raise DagsterError(f"No component type named {name}")
        return self._component_registry.get(name)

    def list_component_types(self) -> Iterable[tuple[str, type[Component]]]:
        for key in sorted(self._component_registry.keys()):
            yield key, self._component_registry.get(key)

    def get_component_instance_path(self, name: str) -> str:
        if name not in self.component_instances:
            raise DagsterError(f"No component instance named {name}")
        return os.path.join(self.components_path, name)

    @property
    def components_package_name(self) -> str:
        return self._components_package_name

    @property
    def components_path(self) -> str:
        return str(self._components_path)

    @property
    def component_instances(self) -> Iterable[str]:
        return sorted(os.listdir(self.components_path))

    def has_component_instance(self, name: str) -> bool:
        return os.path.exists(os.path.join(self.components_path, name))
