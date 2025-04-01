import importlib
from pathlib import Path

from dagster import AssetKey
from dagster_components import load_defs

LOCATION_PATH = Path(__file__).parent.parent / "code_locations" / "python_script_location"


def test_load_from_path() -> None:
    module = importlib.import_module(
        "dagster_components_tests.code_locations.python_script_location.defs"
    )
    defs = load_defs(module)

    assert defs.get_asset_graph().get_all_asset_keys() == {
        AssetKey("a"),
        AssetKey("b"),
        AssetKey("c"),
        AssetKey("up1"),
        AssetKey("up2"),
        AssetKey("override_key"),
        AssetKey("cool_script"),
    }


def test_load_from_location_path() -> None:
    module = importlib.import_module(
        "dagster_components_tests.code_locations.python_script_location.defs.scripts"
    )
    defs = load_defs(module)

    assert defs.get_asset_graph().get_all_asset_keys() == {
        AssetKey("a"),
        AssetKey("b"),
        AssetKey("c"),
        AssetKey("up1"),
        AssetKey("up2"),
        AssetKey("override_key"),
    }
