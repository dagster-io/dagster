import importlib
from datetime import timedelta
from pathlib import Path

import dagster as dg
from dagster.components.core.component_tree import LegacyAutoloadingComponentTree

LOCATION_PATH = Path(__file__).parent.parent / "code_locations" / "python_script_location"


def test_load_from_path(snapshot) -> None:
    module = importlib.import_module(
        "dagster_tests.components_tests.code_locations.python_script_location.defs"
    )
    tree = LegacyAutoloadingComponentTree.from_module(
        defs_module=module, project_root=Path(__file__).parent
    )
    snapshot.assert_match(tree.to_string_representation(include_load_and_build_status=True))
    tree.load_root_component()
    snapshot.assert_match(tree.to_string_representation(include_load_and_build_status=True))

    defs = tree.build_defs()
    assert defs.resolve_asset_graph().get_all_asset_keys() == {
        dg.AssetKey("a"),
        dg.AssetKey("b"),
        dg.AssetKey("b_cron"),
        dg.AssetKey("c"),
        dg.AssetKey("up1"),
        dg.AssetKey("up2"),
        dg.AssetKey("override_key"),
        dg.AssetKey("cool_script"),
        dg.AssetKey("a_dash"),
        dg.AssetKey("b_dash"),
        dg.AssetKey("c_dash"),
        dg.AssetKey("up1_dash"),
        dg.AssetKey("up2_dash"),
        dg.AssetKey("override_key_dash"),
        dg.AssetKey("foo"),
        dg.AssetKey("bar"),
        dg.AssetKey("foo_def_py"),
        dg.AssetKey("bar_def_py"),
        dg.AssetKey("from_defs_one"),
        dg.AssetKey("from_defs_two"),
    }
    assert defs.component_tree

    asset_def = defs.get_assets_def(dg.AssetKey("a"))
    assert (
        asset_def.specs_by_key[dg.AssetKey("a")].automation_condition
        == dg.AutomationCondition.eager()
    )
    assert asset_def.specs_by_key[
        dg.AssetKey("a")
    ].freshness_policy == dg.FreshnessPolicy.time_window(
        fail_window=timedelta(days=2), warn_window=timedelta(days=1)
    )
    assert asset_def.specs_by_key[
        dg.AssetKey("b")
    ].automation_condition == dg.AutomationCondition.on_cron("@daily")
    assert asset_def.specs_by_key[
        dg.AssetKey("b")
    ].freshness_policy == dg.FreshnessPolicy.time_window(fail_window=timedelta(days=3))
    assert asset_def.specs_by_key[
        dg.AssetKey("b_cron")
    ].freshness_policy == dg.FreshnessPolicy.cron(
        deadline_cron="0 10 * * *",
        lower_bound_delta=timedelta(hours=1),
    )

    snapshot.assert_match(tree.to_string_representation(include_load_and_build_status=True))


def test_load_from_location_path() -> None:
    module = importlib.import_module(
        "dagster_tests.components_tests.code_locations.python_script_location.defs.scripts"
    )
    defs = dg.load_defs(module, project_root=Path(__file__).parent)

    assert defs.resolve_asset_graph().get_all_asset_keys() == {
        dg.AssetKey("a"),
        dg.AssetKey("b"),
        dg.AssetKey("b_cron"),
        dg.AssetKey("c"),
        dg.AssetKey("up1"),
        dg.AssetKey("up2"),
        dg.AssetKey("override_key"),
    }
