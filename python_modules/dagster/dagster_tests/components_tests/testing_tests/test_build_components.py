from pathlib import Path

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.definitions_class import Definitions
from dagster.components.component.component import Component
from dagster.components.test.build_components import (
    build_component_at_defs_path,
    build_component_defs_at_defs_path,
)
from dagster_tests.components_tests.testing_tests.utils import (
    defs_for_test_file,
    get_dagster_relative_path,
    get_dagster_test_component_load_context,
)


def get_dagster_module_root() -> Path:
    return Path(__file__).parent.parent.parent.parent


def defs_for_current_test_file() -> Definitions:
    return defs_for_test_file(get_dagster_module_root(), Path(__file__))


# This is what tests will look like it you following this pattern
def test_what_test_will_look_like():
    defs = defs_for_current_test_file()
    assert defs.get_assets_def("my_asset").key == AssetKey("my_asset")


def test_build_single_asset_python_module() -> None:
    context = get_dagster_test_component_load_context()
    defs_path = "dagster_tests/components_tests/testing_tests/test_build_components/my_asset.py"
    component = build_component_at_defs_path(context, defs_path)
    assert isinstance(component, Component)

    defs = build_component_defs_at_defs_path(context, defs_path)
    assert defs.get_assets_def("my_asset").key == AssetKey("my_asset")


def test_build_components_python_subpackage() -> None:
    context = get_dagster_test_component_load_context()
    defs_path = "dagster_tests/components_tests/testing_tests/test_build_components"
    component = build_component_at_defs_path(context, defs_path)
    assert isinstance(component, Component)

    defs = build_component_defs_at_defs_path(context, defs_path)
    assert defs.get_assets_def("my_asset").key == AssetKey("my_asset")


def test_dagster_relative_root_path() -> None:
    path = get_dagster_relative_path(get_dagster_module_root(), Path(__file__))
    assert str(path) == str(
        Path("dagster_tests/components_tests/testing_tests/test_build_components")
    )


def test_build_relative_path_with_defs_path() -> None:
    # This is how I imagine most tests getting wriitten
    defs = defs_for_current_test_file()
    assert defs.get_assets_def("my_asset").key == AssetKey("my_asset")
