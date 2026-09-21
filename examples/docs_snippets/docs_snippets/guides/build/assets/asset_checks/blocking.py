from dagster import AssetCheckResult, Definitions, asset, asset_check


@asset
def upstream_asset():
    pass


@asset_check(asset=upstream_asset, blocking=True)
def check_upstream_asset():
    return AssetCheckResult(passed=False)


@asset(deps=[upstream_asset])
def downstream_asset():
    pass


defs = Definitions(
    assets=[upstream_asset, downstream_asset], asset_checks=[check_upstream_asset]
)
