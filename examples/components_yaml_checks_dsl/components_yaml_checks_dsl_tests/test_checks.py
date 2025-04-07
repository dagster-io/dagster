import dagster as dg
import pandas as pd
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.materialize import materialize

from components_yaml_checks_dsl.definitions import defs
from components_yaml_checks_dsl.lib import HooliAssetChecksComponent
from components_yaml_checks_dsl.lib.hooli_asset_checks.component import StaticThresholdCheck


def checks_specs_by_key(defs: Definitions) -> dict[AssetCheckKey, AssetCheckSpec]:
    """Return a dictionary of check specs by key."""
    return {spec.key: spec for spec in defs.get_all_asset_check_specs()}


def raw_ck(table: str, check_name: str) -> AssetCheckKey:
    """Return an AssetCheckKey for the given table and check name."""
    return AssetCheckKey(
        asset_key=AssetKey(["RAW_DATA", table]),
        name=check_name,
    )


def test_load_defs() -> None:
    defs_obj = defs()
    assert isinstance(defs_obj, Definitions)

    assert defs_obj.get_repository_def()

    assert AssetKey(["RAW_DATA", "users"]) in {spec.key for spec in defs_obj.get_all_asset_specs()}

    check_specs = checks_specs_by_key(defs_obj)
    assert raw_ck("users", "user_count_static_threshold") in check_specs


def test_execute_component() -> None:
    @dg.asset
    def upstream() -> pd.DataFrame:
        return pd.DataFrame({"amount": [100, 200, 300]})

    component = HooliAssetChecksComponent(
        checks=[
            StaticThresholdCheck(
                type="static_threshold",
                check_name="user_count_static_threshold",
                asset="upstream",
                metric="sum:amount",
                min=500,
            )
        ]
    )

    defs = Definitions.merge(component.build_test_defs(), Definitions([upstream]))

    assert AssetKey("upstream") in {spec.key for spec in defs.get_all_asset_specs()}

    assert defs.get_repository_def()

    check_def = defs.get_asset_checks_def(
        AssetCheckKey(AssetKey("upstream"), "user_count_static_threshold")
    )

    result = materialize([upstream, check_def])

    assert result
