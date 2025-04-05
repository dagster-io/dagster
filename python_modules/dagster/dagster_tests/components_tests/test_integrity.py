import importlib

from dagster.components import Component
from dagster.components.core.package_entry import get_package_objects_in_module

_COMPONENT_LIBRARY_MODULES = [
    "dagster",
    "dagster_test.components",
]


def test_all_components_have_component_suffix():
    for module_name in _COMPONENT_LIBRARY_MODULES:
        module = importlib.import_module(module_name)
        for name, obj in get_package_objects_in_module(module):
            if isinstance(obj, type) and issubclass(obj, Component):
                assert name.endswith(
                    "Component"
                ), f"Component {name} in module {module_name} does not have 'Component' suffix"
