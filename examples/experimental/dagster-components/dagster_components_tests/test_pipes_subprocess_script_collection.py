from pathlib import Path

from dagster import AssetKey
from dagster_components.core.component_decl_builder import DefsFileModel
from dagster_components.core.component_defs_builder import (
    YamlComponentDecl,
    build_components_from_component_folder,
    defs_from_components,
)
from dagster_components.impls.pipes_subprocess_script_collection import (
    PipesSubprocessScriptCollection,
)

from dagster_components_tests.utils import assert_assets, get_asset_keys, script_load_context

LOCATION_PATH = Path(__file__).parent / "code_locations" / "python_script_location"


def test_python_native() -> None:
    component = PipesSubprocessScriptCollection.introspect_from_path(
        LOCATION_PATH / "components" / "scripts"
    )
    assert_assets(component, 3)


def test_python_params() -> None:
    component = PipesSubprocessScriptCollection.from_decl_node(
        load_context=script_load_context(),
        component_decl=YamlComponentDecl(
            path=LOCATION_PATH / "components" / "scripts",
            defs_file_model=DefsFileModel(
                component_type="pipes_subprocess_script_collection",
                component_params={
                    "scripts": [
                        {
                            "path": "script_one.py",
                            "assets": [{"key": "a"}, {"key": "b", "deps": ["up1", "up2"]}],
                        },
                        {"path": "subdir/script_three.py", "assets": [{"key": "key_override"}]},
                    ]
                },
            ),
        ),
    )
    assert get_asset_keys(component) == {
        AssetKey("a"),
        AssetKey("b"),
        AssetKey("up1"),
        AssetKey("up2"),
        AssetKey("key_override"),
    }


def test_load_from_path() -> None:
    components = build_components_from_component_folder(
        script_load_context(), LOCATION_PATH / "components"
    )
    assert len(components) == 1
    assert get_asset_keys(components[0]) == {
        AssetKey("a"),
        AssetKey("b"),
        AssetKey("c"),
        AssetKey("up1"),
        AssetKey("up2"),
        AssetKey("override_key"),
    }

    assert_assets(components[0], 6)

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
    }
