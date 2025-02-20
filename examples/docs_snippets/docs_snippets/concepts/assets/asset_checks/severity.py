import dagster as dg


@dg.asset
def my_asset(): ...


@dg.asset_check(asset=my_asset)
def my_check():
    is_serious = ...
    return dg.AssetCheckResult(
        passed=False,
        severity=dg.AssetCheckSeverity.ERROR
        if is_serious
        else dg.AssetCheckSeverity.WARN,
    )


defs = dg.Definitions(assets=[my_asset], asset_checks=[my_check])
