from dagster import AssetKey, Definitions, ExecuteInProcessResult, asset, asset_check
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_checks import build_blocking_asset_check


def execute_assets_and_checks(
    assets=None, asset_checks=None, raise_on_error: bool = True, resources=None, instance=None
) -> ExecuteInProcessResult:
    defs = Definitions(assets=assets, asset_checks=asset_checks, resources=resources)
    job_def = defs.get_implicit_global_asset_job_def()
    return job_def.execute_in_process(raise_on_error=raise_on_error, instance=instance)


def test_blocking():
    @asset
    def my_asset():
        pass

    @asset_check(asset="my_asset")
    def pass_check():
        return AssetCheckResult(success=True, check_name="pass_check")

    @asset_check(asset="my_asset")
    def fail_check():
        return AssetCheckResult(success=False, check_name="fail_check")

    blocking_asset = build_blocking_asset_check(asset_def=my_asset, checks=[pass_check, fail_check])

    @asset(deps=[blocking_asset])
    def downstream_asset():
        pass

    result = execute_assets_and_checks(
        assets=[blocking_asset, downstream_asset], raise_on_error=False
    )
    assert not result.success

    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 2
    check_evals_by_name = {check_eval.check_name: check_eval for check_eval in check_evals}
    assert check_evals_by_name["pass_check"].success
    assert check_evals_by_name["pass_check"].asset_key == AssetKey(["my_asset"])
    assert not check_evals_by_name["fail_check"].success
    assert check_evals_by_name["fail_check"].asset_key == AssetKey(["my_asset"])

    # downstream asset should not have been materialized
    materialization_events = result.get_asset_materialization_events()
    assert len(materialization_events) == 1
    assert materialization_events[0].asset_key == AssetKey(["my_asset"])
