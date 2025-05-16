from dagster._core.definitions.asset_key import AssetKey
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.test.build_components import (
    build_component_at_path,
    build_component_defs_at_path,
)
from dagster_tests.components_tests.testing_tests.utils import (
    get_dagster_test_component_load_context,
)


def test_build_single_asset_python_module() -> None:
    context = get_dagster_test_component_load_context()
    assert isinstance(context, ComponentLoadContext)

    component = build_component_at_path(context, "single_definitions/my_asset.py")
    assert isinstance(component, Component)

    defs = build_component_defs_at_path(context, "single_definitions/my_asset.py")
    assert defs.get_assets_def("my_asset").key == AssetKey("my_asset")


def test_build_components_python_subpackage() -> None:
    context = get_dagster_test_component_load_context()
    defs = build_component_defs_at_path(context, "single_definitions")
    assert defs.get_assets_def("my_asset").key == AssetKey("my_asset")
