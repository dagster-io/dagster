from collections.abc import Iterable

import dagster as dg


@dg.multi_asset_check(
    specs=[
        dg.AssetCheckSpec(name="asset_check_one", asset="my_asset_one"),
        dg.AssetCheckSpec(name="asset_check_two", asset="my_asset_two"),
    ]
)
def the_check(context: dg.AssetCheckExecutionContext) -> Iterable[dg.AssetCheckResult]:
    yield dg.AssetCheckResult(
        passed=False,
        severity=dg.AssetCheckSeverity.WARN,
        description="The asset is over 0.5",
        asset_key="asset_check_one",
    )

    yield dg.AssetCheckResult(
        passed=True,
        description="The asset is fresh.",
        asset_key="asset_check_two",
    )
