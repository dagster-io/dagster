import dagster as dg


@dg.asset(check_specs=[dg.AssetCheckSpec(name="in_op_check", asset="asset_1")])
def asset_1():
    yield dg.Output(1)
    yield dg.AssetCheckResult(passed=True)


@dg.asset_check(asset=asset_1)
def asset_check_1(asset_1):
    return dg.AssetCheckResult(passed=True)


# duplicate asset specs in scope shouldn't error
asset_specs = [dg.AssetSpec("asset_1"), dg.AssetSpec("asset_1")]
