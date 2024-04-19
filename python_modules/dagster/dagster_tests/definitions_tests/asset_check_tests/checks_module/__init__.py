from dagster import AssetCheckResult, AssetCheckSpec, Output, asset, asset_check


@asset(check_specs=[AssetCheckSpec(name="in_op_check", asset="asset_1")])
def asset_1():
    yield Output(1)
    yield AssetCheckResult(passed=True)


@asset_check(asset=asset_1)
def asset_check_1(asset_1):
    return AssetCheckResult(passed=True)
