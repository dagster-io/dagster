from pathlib import Path

from dagster import AssetKey
from dagster_components import AssetAttributesModel
from dagster_components.core.component_decl_builder import ComponentFileModel, YamlComponentDecl
from dagster_components.core.component_defs_builder import (
    build_components_from_component_folder,
    build_defs_from_component_path,
    defs_from_components,
)
from dagster_components.lib.pipes_subprocess_script_collection import (
    PipesSubprocessScriptCollection,
    PipesSubprocessScriptCollectionParams,
    PipesSubprocessScriptParams,
)

from dagster_components_tests.utils import assert_assets, get_asset_keys, script_load_context

LOCATION_PATH = Path(__file__).parent.parent / "code_locations" / "python_script_location"


def test_python_native() -> None:
    component = PipesSubprocessScriptCollection.introspect_from_path(
        LOCATION_PATH / "components" / "scripts"
    )
    assert_assets(component, 3)


def test_python_params() -> None:
    params = PipesSubprocessScriptCollectionParams(
        scripts=[
            PipesSubprocessScriptParams(
                path="script_one.py",
                assets=[
                    AssetAttributesModel(
                        key="a", automation_condition="{{ automation_condition.eager() }}"
                    ),
                    AssetAttributesModel(
                        key="b",
                        automation_condition="{{ automation_condition.on_cron('@daily') }}",
                        deps=["up1", "up2"],
                    ),
                ],
            ),
            PipesSubprocessScriptParams(
                path="subdir/script_three.py",
                assets=[AssetAttributesModel(key="key_override")],
            ),
        ]
    )
    component = PipesSubprocessScriptCollection.load(
        params=params,
        # TODO: we should use a PythonComponentDecl here instead
        context=script_load_context(
            YamlComponentDecl(
                path=Path(LOCATION_PATH / "components" / "scripts"),
                component_file_model=ComponentFileModel(type="."),
            )
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
