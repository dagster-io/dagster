from collections.abc import Iterable

import dagster as dg


@dg.multi_asset_check(
    specs=[
        dg.AssetCheckSpec(name="asset_check_one", asset="asset_one"),
        dg.AssetCheckSpec(name="asset_check_two", asset="asset_two"),
    ],
    can_subset=True,
)
def the_check(context: dg.AssetCheckExecutionContext) -> Iterable[dg.AssetCheckResult]:
    if (
        dg.AssetCheckKey(dg.AssetKey("asset_one"), "asset_check_one")
        in context.selected_asset_check_keys
    ):
        yield dg.AssetCheckResult(
            passed=True, metadata={"foo": "bar"}, check_name="asset_check_one"
        )
    if (
        dg.AssetCheckKey(dg.AssetKey("asset_two"), "asset_check_two")
        in context.selected_asset_check_keys
    ):
        yield dg.AssetCheckResult(
            passed=True, metadata={"foo": "bar"}, check_name="asset_check_two"
        )
