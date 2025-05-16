from pathlib import Path

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.definitions_class import Definitions
from dagster.components.component.component import Component
from dagster.components.test.build_components import (
    build_component_at_path,
    build_component_defs_at_path,
)
from dagster_tests.components_tests.testing_tests.utils import (
    get_dagster_test_component_load_context,
)


def get_dagster_module_root() -> Path:
    return Path(__file__).parent.parent.parent.parent


def get_dagster_relative_path(path: Path) -> Path:
    relative_path = path.relative_to(get_dagster_module_root())
    if relative_path.suffix == ".py":
        relative_path = relative_path.with_suffix("")

    return relative_path


def test_build_single_asset_python_module() -> None:
    context = get_dagster_test_component_load_context()
    defs_path = "dagster_tests/components_tests/testing_tests/test_build_components/my_asset.py"
    component = build_component_at_path(context, defs_path)
    assert isinstance(component, Component)

    defs = build_component_defs_at_path(context, defs_path)
    assert defs.get_assets_def("my_asset").key == AssetKey("my_asset")


def test_build_components_python_subpackage() -> None:
    context = get_dagster_test_component_load_context()
    defs_path = "dagster_tests/components_tests/testing_tests/test_build_components"
    component = build_component_at_path(context, defs_path)
    assert isinstance(component, Component)

    defs = build_component_defs_at_path(context, defs_path)
    assert defs.get_assets_def("my_asset").key == AssetKey("my_asset")


def test_dagster_relative_root_path() -> None:
    path = get_dagster_relative_path(Path(__file__))
    assert str(path) == str(
        Path("dagster_tests/components_tests/testing_tests/test_build_components")
    )


def defs_path_in_dagster_test_project(dunderfile_path: Path) -> Path:
    return get_dagster_relative_path(dunderfile_path)


def defs_for_current_test_file() -> Definitions:
    return build_component_defs_at_path(
        get_dagster_test_component_load_context(),
        defs_path=defs_path_in_dagster_test_project(Path(__file__)),
    )


def test_build_relative_path_with_defs_path() -> None:
    # This is how I imagine most tests getting wriitten
    defs = defs_for_current_test_file()
    assert defs.get_assets_def("my_asset").key == AssetKey("my_asset")
