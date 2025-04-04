from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.materialize import materialize
from dagster.components import ComponentLoadContext

from components_yaml_checks_dsl.definitions import defs
from components_yaml_checks_dsl.lib import HooliAssetChecksComponent
from components_yaml_checks_dsl.lib.hooli_asset_checks.component import HooliAssetCheck


def checks_specs_by_key(defs: Definitions) -> dict[str, AssetCheckSpec]:
    """Return a dictionary of check specs by key."""
    check_specs = {}
    asset_graph = defs.get_asset_graph()

    for check_key in asset_graph.asset_check_keys:
        check_spec = asset_graph.get_check_spec(check_key)
        check_specs[check_key] = check_spec
    return check_specs


def raw_ck(table: str, check_name: str) -> AssetCheckKey:
    """Return an AssetCheckKey for the given table and check name."""
    return AssetCheckKey(
        asset_key=AssetKey(["RAW_DATA", table]),
        name=check_name,
    )


def test_load_defs() -> None:
    defs_obj = defs()
    assert isinstance(defs_obj, Definitions)

    check_specs = checks_specs_by_key(defs_obj)
    assert raw_ck("users", "user_count_static_threshold") in check_specs


def get_check_def(
    component: HooliAssetChecksComponent, key: AssetCheckKey
) -> AssetChecksDefinition:
    context = ComponentLoadContext.for_test()
    defs = component.build_defs(context)
    assets_def = defs.get_asset_graph().assets_def_for_key(key)
    assert isinstance(assets_def, AssetChecksDefinition)
    return assets_def


def test_execute_component() -> None:
    component = HooliAssetChecksComponent(
        checks=[
            HooliAssetCheck(
                type="static_threshold",
                check_name="user_count_static_threshold",
                asset="RAW_DATA.users",
                metric="num_rows",
                min=500,
            )
        ]
    )

    check_def = get_check_def(component, raw_ck("users", "user_count_static_threshold"))

    result = materialize([check_def])

    assert result
