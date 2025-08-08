import importlib
import sys
from pathlib import Path

import dagster as dg

CROSS_COMPONENT_DEPENDENCY_PATH = (
    Path(__file__).parent.parent / "code_locations" / "component_component_deps"
)


def test_dependency_between_components():
    sys.path.append(str(CROSS_COMPONENT_DEPENDENCY_PATH.parent))

    defs_root = importlib.import_module(f"{CROSS_COMPONENT_DEPENDENCY_PATH.name}.defs")
    defs = dg.load_defs(defs_root=defs_root, project_root=CROSS_COMPONENT_DEPENDENCY_PATH.parent)
    assert (
        dg.AssetKey("downstream_of_all_my_python_defs")
        in defs.resolve_asset_graph().get_all_asset_keys()
    )
    downstream_of_all_my_python_defs = defs.resolve_assets_def("downstream_of_all_my_python_defs")
    assert set(
        downstream_of_all_my_python_defs.asset_deps[dg.AssetKey("downstream_of_all_my_python_defs")]
    ) == set(defs.resolve_asset_graph().get_all_asset_keys()) - {
        dg.AssetKey("downstream_of_all_my_python_defs")
    }


CROSS_COMPONENT_DEPENDENCY_PATH_CUSTOM_COMPONENT = (
    Path(__file__).parent.parent / "code_locations" / "component_component_deps_custom_component"
)


def test_dependency_between_components_with_custom_component():
    sys.path.append(str(CROSS_COMPONENT_DEPENDENCY_PATH_CUSTOM_COMPONENT.parent))

    defs_root = importlib.import_module(
        f"{CROSS_COMPONENT_DEPENDENCY_PATH_CUSTOM_COMPONENT.name}.defs"
    )
    defs = dg.load_defs(
        defs_root=defs_root, project_root=CROSS_COMPONENT_DEPENDENCY_PATH_CUSTOM_COMPONENT.parent
    )
    assert (
        dg.AssetKey("downstream_of_all_my_python_defs")
        in defs.resolve_asset_graph().get_all_asset_keys()
    )
    downstream_of_all_my_python_defs = defs.resolve_assets_def("downstream_of_all_my_python_defs")
    assert set(
        downstream_of_all_my_python_defs.asset_deps[dg.AssetKey("downstream_of_all_my_python_defs")]
    ) == set(defs.resolve_asset_graph().get_all_asset_keys()) - {
        dg.AssetKey("downstream_of_all_my_python_defs")
    }


CROSS_COMPONENT_DEPENDENCY_PATH_YAML = (
    Path(__file__).parent.parent / "code_locations" / "component_component_deps_yaml"
)


def test_dependency_between_components_with_yaml():
    sys.path.append(str(CROSS_COMPONENT_DEPENDENCY_PATH_YAML.parent))

    defs_root = importlib.import_module(f"{CROSS_COMPONENT_DEPENDENCY_PATH_YAML.name}.defs")
    defs = dg.load_defs(
        defs_root=defs_root, project_root=CROSS_COMPONENT_DEPENDENCY_PATH_YAML.parent
    )
    assert (
        dg.AssetKey("downstream_of_all_my_python_defs")
        in defs.resolve_asset_graph().get_all_asset_keys()
    )
    downstream_of_all_my_python_defs = defs.resolve_assets_def("downstream_of_all_my_python_defs")
    assert set(
        downstream_of_all_my_python_defs.asset_deps[dg.AssetKey("downstream_of_all_my_python_defs")]
    ) == set(defs.resolve_asset_graph().get_all_asset_keys()) - {
        dg.AssetKey("downstream_of_all_my_python_defs")
    }
