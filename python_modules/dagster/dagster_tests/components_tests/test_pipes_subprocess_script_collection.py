from pathlib import Path

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
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.declarative_automation.operators.dep_operators import (
    AnyDepsCondition,
)

LOCATION_PATH = Path(__file__).parent / "code_locations" / "python_script_location"


def registry() -> ComponentRegistry:
    return ComponentRegistry(
        {"pipes_subprocess_script_collection": PipesSubprocessScriptCollection}
    )


def script_load_context() -> ComponentLoadContext:
    return ComponentLoadContext(registry=registry(), resources={})


def _assert_assets(component: Component, expected_assets: int) -> None:
    defs = component.build_defs(ComponentLoadContext.for_test())
    assert len(defs.get_asset_graph().get_all_asset_keys()) == expected_assets
    result = defs.get_implicit_global_asset_job_def().execute_in_process()
    assert result.success


def test_python_native() -> None:
    component = PipesSubprocessScriptCollection(LOCATION_PATH / "components" / "scripts")
    _assert_assets(component, 3)


def load_component_with_params(component_params: dict) -> PipesSubprocessScriptCollection:
    return PipesSubprocessScriptCollection.from_decl_node(
        load_context=script_load_context(),
        component_decl=YamlComponentDecl(
            path=LOCATION_PATH / "components" / "scripts",
            defs_file_model=DefsFileModel(
                component_type="pipes_subprocess_script_collection",
                component_params=component_params,
            ),
        ),
    )


def test_python_params() -> None:
    component = load_component_with_params(
        component_params={
            "script_one": {
                "assets": [
                    {"key": "a"},
                    {"key": "b", "deps": ["up1", "up2"]},
                ]
            },
            "script_three": {"assets": [{"key": "key_override"}]},
        },
    )
    _assert_assets(component, 6)


def test_load_from_path() -> None:
    components = build_components_from_component_folder(
        script_load_context(), LOCATION_PATH / "components"
    )
    assert len(components) == 1

    _assert_assets(components[0], 6)


def test_build_from_path() -> None:
    components = build_components_from_component_folder(
        script_load_context(), LOCATION_PATH / "components"
    )

    defs = defs_from_components(
        context=script_load_context(),
        components=components,
        resources={},
    )

    assert len(defs.get_asset_graph().get_all_asset_keys()) == 6


def test_cron_automation_condition() -> None:
    component = load_component_with_params(
        component_params={
            "script_one": {
                "assets": [
                    {
                        "key": "a",
                        "automation_condition": "on_cron('0 0 * * *', 'UTC')",
                    },
                ]
            },
        },
    )

    defs = defs_from_components(
        context=script_load_context(),
        components=[component],
        resources={},
    )

    a_key = AssetKey("a")

    a_spec = defs.get_assets_def(a_key).get_asset_spec(a_key)
    assert a_spec.automation_condition
    assert a_spec.automation_condition.get_label() == "on_cron(0 0 * * *, UTC)"


def test_eager_automation_condition() -> None:
    component = load_component_with_params(
        component_params={
            "script_one": {
                "assets": [
                    {"key": "a", "automation_condition": "eager()"},
                ]
            },
        },
    )

    defs = defs_from_components(
        context=script_load_context(),
        components=[component],
        resources={},
    )

    a_key = AssetKey("a")

    a_spec = defs.get_assets_def(a_key).get_asset_spec(a_key)
    assert a_spec.automation_condition
    assert a_spec.automation_condition.get_label() == "eager"


def test_more_complex_condition() -> None:
    component = load_component_with_params(
        component_params={
            "script_one": {
                "assets": [
                    {
                        "key": "a",
                        "automation_condition": "any_deps_match(in_progress() | execution_failed())",
                    },
                ]
            },
        },
    )

    defs = defs_from_components(
        context=script_load_context(),
        components=[component],
        resources={},
    )

    a_key = AssetKey("a")

    a_spec = defs.get_assets_def(a_key).get_asset_spec(a_key)
    assert a_spec.automation_condition
    assert isinstance(a_spec.automation_condition, AnyDepsCondition)
