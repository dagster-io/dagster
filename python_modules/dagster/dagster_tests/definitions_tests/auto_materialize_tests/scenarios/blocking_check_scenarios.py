from dagster import AssetCheckResult, AutoMaterializePolicy, asset, asset_check
from dagster._core.definitions.asset_checks import build_asset_with_blocking_check

from ..base_scenario import (
    AssetReconciliationScenario,
    run,
    run_request,
)


@asset(auto_materialize_policy=AutoMaterializePolicy.eager())
def asset1():
    pass


@asset_check(asset=asset1)
def asset1_check():
    return AssetCheckResult(passed=False)


asset1_with_blocking_check = build_asset_with_blocking_check(asset1, [asset1_check])


@asset(auto_materialize_policy=AutoMaterializePolicy.eager(), deps=[asset1_with_blocking_check])
def asset2():
    pass


@asset(auto_materialize_policy=AutoMaterializePolicy.eager(), deps=[asset2])
def asset3():
    pass


# AMP currently doesn't respect blocking checks. The blocking check will stop downstreams if they're
# in the same run, but not if they're in a different run.

blocking_check_scenarios = {
    "blocking_check_works_inside_run": AssetReconciliationScenario(
        assets=[asset1_with_blocking_check, asset2, asset3],
        unevaluated_runs=[run(["asset1"]), run(["asset2"]), run(["asset1", "asset2"])],
        expected_run_requests=[],
    ),
    "blocking_check_doesnt_work_across_runs": AssetReconciliationScenario(
        assets=[asset1_with_blocking_check, asset2, asset3],
        unevaluated_runs=[run(["asset1"])],
        expected_run_requests=[run_request(asset_keys=["asset2", "asset3"])],
    ),
}
