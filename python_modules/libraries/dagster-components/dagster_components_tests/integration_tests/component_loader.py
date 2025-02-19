import importlib
import sys
from pathlib import Path
from typing import Optional

from dagster._core.definitions.definitions_class import Definitions
from dagster_components.core.component import (
    ComponentTypeRegistry,
    get_component_type_name,
    get_registered_component_types_in_module,
)
from dagster_components.core.component_defs_builder import build_defs_from_component_path
from dagster_components.core.component_key import GlobalComponentKey

from dagster_components_tests.utils import create_code_location_from_components


def load_test_component_defs(
    src_path: str, local_component_defn_to_inject: Optional[Path] = None
) -> Definitions:
    """Loads a component from a test component project, making the provided local component defn
    available in that component's __init__.py.
    """
    with create_code_location_from_components(
        src_path, local_component_defn_to_inject=local_component_defn_to_inject
    ) as code_location_dir:
        registry = load_test_component_project_registry(include_test=True)

        sys.path.append(str(code_location_dir))

        return build_defs_from_component_path(
            components_root=Path(code_location_dir) / "my_location" / "components",
            path=Path(code_location_dir) / "my_location" / "components" / Path(src_path).stem,
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
            key = GlobalComponentKey(
                name=get_component_type_name(component),
                namespace=f"dagster_components{'.test' if package_name.endswith('test') else ''}",
            )
            components[key] = component
    return ComponentTypeRegistry(components)
