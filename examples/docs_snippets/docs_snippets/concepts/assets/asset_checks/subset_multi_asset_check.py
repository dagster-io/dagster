import random
from typing import Iterable

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
    ],
    can_subset=True,
)
def the_check(context: AssetCheckExecutionContext) -> Iterable[AssetCheckResult]:
    for check_key in context.selected_asset_check_keys:
        asset_key = check_key.asset_key

        # TODO: populate metadata
        metadata = {}
        if random.random() > 0.5:
            yield AssetCheckResult(
                passed=False,
                severity=AssetCheckSeverity.WARN,
                description="The asset is over 0.5",
                asset_key=asset_key,
            )
        else:
            yield AssetCheckResult(
                passed=True,
                metadata=metadata,
                description="The asset is fresh.",
                asset_key=asset_key,
            )
