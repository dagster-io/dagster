import importlib

from dagster_components.core.component import get_component_types_in_module

_COMPONENT_LIBRARY_MODULES = [
    "dagster_components",
    "dagster_test.components",
]


def test_all_components_have_component_suffix():
    for module_name in _COMPONENT_LIBRARY_MODULES:
        module = importlib.import_module(module_name)
        for name, _ in get_component_types_in_module(module):
            assert name.endswith("Component"), (
                f"Component {name} in module {module_name} does not have 'Component' suffix"
            )
