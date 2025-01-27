import importlib
from pathlib import Path

from dagster._core.definitions.definitions_class import Definitions
from dagster_components.core.component import (
    ComponentTypeRegistry,
    get_component_type_name,
    get_registered_component_types_in_module,
)
from dagster_components.core.component_defs_builder import build_defs_from_component_path
from dagster_components.core.deployment import CodeLocationProjectContext


def load_test_component_defs(name: str) -> Definitions:
    context = load_test_component_project_context()
    return build_defs_from_component_path(
        path=Path(__file__).parent / "components" / name,
        registry=context.component_registry,
        resources={},
    )


def load_test_component_project_context(include_test: bool = False) -> CodeLocationProjectContext:
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

    return CodeLocationProjectContext(
        root_path=str(Path(__file__).parent),
        name="test",
        root_package=Path(__file__).parent.name.replace("-", "_"),
        component_registry=ComponentTypeRegistry(components),
        components_path=Path(__file__).parent / "components",
        components_package_name="dagster_components_tests.integration_tests.components",
    )
