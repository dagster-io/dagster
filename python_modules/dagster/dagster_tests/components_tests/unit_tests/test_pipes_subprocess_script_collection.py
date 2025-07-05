import importlib
from pathlib import Path

from dagster import AssetKey, load_defs

LOCATION_PATH = Path(__file__).parent.parent / "code_locations" / "python_script_location"


def test_load_from_path() -> None:
    module = importlib.import_module(
        "dagster_tests.components_tests.code_locations.python_script_location.defs"
    )
    defs = load_defs(module, project_root=Path(__file__).parent)

    assert defs.resolve_asset_graph().get_all_asset_keys() == {
        AssetKey("a"),
        AssetKey("b"),
        AssetKey("c"),
        AssetKey("up1"),
        AssetKey("up2"),
        AssetKey("override_key"),
        AssetKey("cool_script"),
        AssetKey("a_dash"),
        AssetKey("b_dash"),
        AssetKey("c_dash"),
        AssetKey("up1_dash"),
        AssetKey("up2_dash"),
        AssetKey("override_key_dash"),
        AssetKey("foo"),
        AssetKey("bar"),
        AssetKey("foo_def_py"),
        AssetKey("bar_def_py"),
        AssetKey("from_defs_one"),
        AssetKey("from_defs_two"),
    }
    assert defs.component_tree


def test_load_from_location_path() -> None:
    module = importlib.import_module(
        "dagster_tests.components_tests.code_locations.python_script_location.defs.scripts"
    )
    defs = load_defs(module, project_root=Path(__file__).parent)

    assert defs.resolve_asset_graph().get_all_asset_keys() == {
        AssetKey("a"),
        AssetKey("b"),
        AssetKey("c"),
        AssetKey("up1"),
        AssetKey("up2"),
        AssetKey("override_key"),
    }
