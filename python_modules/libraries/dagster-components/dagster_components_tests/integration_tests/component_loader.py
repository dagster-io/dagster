import importlib
from pathlib import Path

from dagster._core.definitions.definitions_class import Definitions
from dagster_components.core.component import (
    ComponentTypeRegistry,
    get_component_type_name,
    get_registered_component_types_in_module,
)
from dagster_components.core.component_defs_builder import build_defs_from_component_path


def load_test_component_defs(name: str) -> Definitions:
    registry = load_test_component_project_registry()
    return build_defs_from_component_path(
        path=Path(__file__).parent / "components" / name,
        registry=registry,
        resources={},
    )


def load_test_component_project_registry(include_test: bool = False) -> ComponentTypeRegistry:
    components = {}
    package_name = "dagster_components.lib"

    packages = ["dagster_components.lib"] + (
        ["dagster_components.lib.test"] if include_test else []
    )
    for package_name in packages:
        dc_module = importlib.import_module(package_name)

        for component in get_registered_component_types_in_module(dc_module):
            key = f"dagster_components.{'test.' if package_name.endswith('test') else ''}{get_component_type_name(component)}"
            components[key] = component
    return ComponentTypeRegistry(components)
