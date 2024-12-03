from pathlib import Path

from dagster import AssetKey
from dagster._components.core.component import Component, ComponentLoadContext, ComponentRegistry
from dagster._components.core.component_decl_builder import DefsFileModel
from dagster._components.core.component_defs_builder import (
    YamlComponentDecl,
    build_components_from_component_folder,
    defs_from_components,
)
from dagster._components.impls.pipes_subprocess_script_collection import (
    PipesSubprocessScriptCollection,
)
from dagster._core.instance import DagsterInstance

LOCATION_PATH = Path(__file__).parent / "code_locations" / "python_script_location"


def registry() -> ComponentRegistry:
    return ComponentRegistry(
        {"pipes_subprocess_script_collection": PipesSubprocessScriptCollection}
    )


def script_load_context() -> ComponentLoadContext:
    return ComponentLoadContext(registry=registry(), resources={})


def _asset_keys(component: Component) -> set[AssetKey]:
    return {
        key
        for key in component.build_defs(ComponentLoadContext.for_test())
        .get_asset_graph()
        .get_all_asset_keys()
    }


def _assert_assets(component: Component, expected_assets: int) -> None:
    defs = component.build_defs(ComponentLoadContext.for_test())
    assert len(defs.get_asset_graph().get_all_asset_keys()) == expected_assets
    result = defs.get_implicit_global_asset_job_def().execute_in_process(
        instance=DagsterInstance.ephemeral()
    )
    assert result.success


def test_python_native() -> None:
    component = PipesSubprocessScriptCollection.introspect_from_path(
        LOCATION_PATH / "components" / "scripts"
    )
    _assert_assets(component, 3)


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
    assert _asset_keys(component) == {
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
    assert _asset_keys(components[0]) == {
        AssetKey("a"),
        AssetKey("b"),
        AssetKey("c"),
        AssetKey("up1"),
        AssetKey("up2"),
        AssetKey("override_key"),
    }

    _assert_assets(components[0], 6)

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
