from collections.abc import Iterable

from dagster import (
    AssetCheckExecutionContext,
    AssetCheckResult,
    AssetCheckSeverity,
    AssetCheckSpec,
    multi_asset_check,
)


@multi_asset_check(
    specs=[
        AssetCheckSpec(name="asset_check_one", asset="my_asset_one"),
        AssetCheckSpec(name="asset_check_two", asset="my_asset_two"),
    ]
)
def the_check(context: AssetCheckExecutionContext) -> Iterable[AssetCheckResult]:
    yield AssetCheckResult(
        passed=False,
        severity=AssetCheckSeverity.WARN,
        description="The asset is over 0.5",
        asset_key="asset_check_one",
    )

    yield AssetCheckResult(
        passed=True,
        description="The asset is fresh.",
        asset_key="asset_check_two",
    )
