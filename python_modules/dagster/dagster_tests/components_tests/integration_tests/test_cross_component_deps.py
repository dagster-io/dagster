import sys
from pathlib import Path

from dagster._core.definitions.asset_key import AssetKey
from dagster.components import build_component_defs

CROSS_COMPONENT_DEPENDENCY_PATH = (
    Path(__file__).parent.parent / "code_locations" / "component_component_deps"
)


def test_dependency_between_components():
    sys.path.append(str(CROSS_COMPONENT_DEPENDENCY_PATH.parent))

    defs = build_component_defs(CROSS_COMPONENT_DEPENDENCY_PATH / "defs")
    assert (
        AssetKey("downstream_of_all_my_python_defs") in defs.get_asset_graph().get_all_asset_keys()
    )
    downstream_of_all_my_python_defs = defs.get_assets_def("downstream_of_all_my_python_defs")
    assert set(
        downstream_of_all_my_python_defs.asset_deps[AssetKey("downstream_of_all_my_python_defs")]
    ) == set(defs.get_asset_graph().get_all_asset_keys()) - {
        AssetKey("downstream_of_all_my_python_defs")
    }


CROSS_COMPONENT_DEPENDENCY_PATH_CUSTOM_COMPONENT = (
    Path(__file__).parent.parent / "code_locations" / "component_component_deps_custom_component"
)


def test_dependency_between_components_with_custom_component():
    sys.path.append(str(CROSS_COMPONENT_DEPENDENCY_PATH_CUSTOM_COMPONENT.parent))

    defs = build_component_defs(CROSS_COMPONENT_DEPENDENCY_PATH_CUSTOM_COMPONENT / "defs")
    assert (
        AssetKey("downstream_of_all_my_python_defs") in defs.get_asset_graph().get_all_asset_keys()
    )
    downstream_of_all_my_python_defs = defs.get_assets_def("downstream_of_all_my_python_defs")
    assert set(
        downstream_of_all_my_python_defs.asset_deps[AssetKey("downstream_of_all_my_python_defs")]
    ) == set(defs.get_asset_graph().get_all_asset_keys()) - {
        AssetKey("downstream_of_all_my_python_defs")
    }
