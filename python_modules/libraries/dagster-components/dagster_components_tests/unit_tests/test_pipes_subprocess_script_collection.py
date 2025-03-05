import importlib
from pathlib import Path

from dagster import AssetKey
from dagster_components import build_component_defs
from dagster_components.core.component_decl_builder import PythonComponentDecl
from dagster_components.core.component_defs_builder import build_defs_from_component_module

from dagster_components_tests.utils import script_load_context

LOCATION_PATH = Path(__file__).parent.parent / "code_locations" / "python_script_location"


def test_python_params() -> None:
    node = PythonComponentDecl(path=Path(LOCATION_PATH / "defs" / "script_python_decl"))
    context = script_load_context(node)
    components = node.load(context)
    assert len(components) == 1
    component = components[0]

    assert component.build_defs(context).get_asset_graph().get_all_asset_keys() == {
        AssetKey("cool_script")
    }


def test_load_from_path() -> None:
    module = importlib.import_module(
        "dagster_components_tests.code_locations.python_script_location.defs"
    )
    defs = build_component_defs(module)

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
    defs = build_defs_from_component_module(module, resources={})

    assert defs.get_asset_graph().get_all_asset_keys() == {
        AssetKey("a"),
        AssetKey("b"),
        AssetKey("c"),
        AssetKey("up1"),
        AssetKey("up2"),
        AssetKey("override_key"),
    }
