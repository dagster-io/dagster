from pathlib import Path

from dagster import AssetKey
from dagster_components.core.component_decl_builder import PythonComponentDecl
from dagster_components.core.component_defs_builder import (
    build_components_from_component_folder,
    build_defs_from_component_path,
    defs_from_components,
)
from dagster_components.lib.pipes_subprocess_script_collection import (
    PipesSubprocessScriptCollection,
)

from dagster_components_tests.utils import assert_assets, get_asset_keys, script_load_context

LOCATION_PATH = Path(__file__).parent.parent / "code_locations" / "python_script_location"


def test_python_native() -> None:
    component = PipesSubprocessScriptCollection.introspect_from_path(
        LOCATION_PATH / "components" / "scripts"
    )
    assert_assets(component, 3)


def test_python_params() -> None:
    node = PythonComponentDecl(path=Path(LOCATION_PATH / "components" / "script_python_decl"))
    context = script_load_context(node)
    components = node.load(context)
    assert len(components) == 1
    component = components[0]

    assert get_asset_keys(component) == {AssetKey("cool_script")}


def test_load_from_path() -> None:
    components = build_components_from_component_folder(
        script_load_context(), LOCATION_PATH / "components"
    )
    assert len(components) == 2

    defs = defs_from_components(
        context=script_load_context(),
        components=components,
        resources={},
    )

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
    defs = build_defs_from_component_path(
        LOCATION_PATH / "components" / "scripts", script_load_context().registry, {}
    )
    assert defs.get_asset_graph().get_all_asset_keys() == {
        AssetKey("a"),
        AssetKey("b"),
        AssetKey("c"),
        AssetKey("up1"),
        AssetKey("up2"),
        AssetKey("override_key"),
    }
