from dagster import (
    AssetCheckResult,
    AssetCheckSeverity,
    Definitions,
    asset,
    asset_check,
)


@asset
def my_asset():
    ...


@asset_check(asset=my_asset)
def my_check():
    is_serious = ...
    return AssetCheckResult(
        success=False,
        severity=AssetCheckSeverity.ERROR if is_serious else AssetCheckSeverity.WARNING,
    )


defs = Definitions(assets=[my_asset], asset_checks=[my_check])
