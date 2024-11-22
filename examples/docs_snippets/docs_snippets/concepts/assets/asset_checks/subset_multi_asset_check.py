from collections.abc import Iterable

from dagster import (
    AssetCheckExecutionContext,
    AssetCheckKey,
    AssetCheckResult,
    AssetCheckSpec,
    AssetKey,
    multi_asset_check,
)


@multi_asset_check(
    specs=[
        AssetCheckSpec(name="asset_check_one", asset="asset_one"),
        AssetCheckSpec(name="asset_check_two", asset="asset_two"),
    ],
    can_subset=True,
)
def the_check(context: AssetCheckExecutionContext) -> Iterable[AssetCheckResult]:
    if (
        AssetCheckKey(AssetKey("asset_one"), "asset_check_one")
        in context.selected_asset_check_keys
    ):
        yield AssetCheckResult(
            passed=True, metadata={"foo": "bar"}, check_name="asset_check_one"
        )
    if (
        AssetCheckKey(AssetKey("asset_two"), "asset_check_two")
        in context.selected_asset_check_keys
    ):
        yield AssetCheckResult(
            passed=True, metadata={"foo": "bar"}, check_name="asset_check_two"
        )
