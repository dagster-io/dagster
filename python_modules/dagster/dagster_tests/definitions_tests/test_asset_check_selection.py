from dagster import (
    AssetCheckHandle,
    AssetCheckResult,
    Definitions,
    ExecuteInProcessResult,
    Selection,
    UnresolvedAssetJobDefinition,
    asset,
    asset_check,
    define_asset_job,
)


@asset
def asset1():
    ...


@asset
def asset2():
    ...


@asset_check(asset=asset1)
def asset1_check1():
    return AssetCheckResult(success=True)


@asset_check(asset=asset1)
def asset1_check2():
    return AssetCheckResult(success=True)


@asset_check(asset=asset1)
def asset2_check1():
    return AssetCheckResult(success=True)


def execute_asset_job_in_process(asset_job: UnresolvedAssetJobDefinition) -> ExecuteInProcessResult:
    assets = [asset1, asset2]
    asset_checks = [asset1_check1, asset1_check2, asset2_check1]
    defs = Definitions(assets=assets, jobs=[asset_job], asset_checks=asset_checks)
    job_def = defs.get_job_def(asset_job.name)
    return job_def.execute_in_process()


def test_job_with_all_checks_no_materializations():
    job_def = define_asset_job("job1", selection=Selection.all_asset_checks())
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 0
    check_evals = result.get_asset_check_evaluations()
    assert {check_eval.handle for check_eval in check_evals} == {
        AssetCheckHandle(asset1.key, "asset1_check1"),
        AssetCheckHandle(asset1.key, "asset1_check2"),
        AssetCheckHandle(asset2.key, "asset2_check1"),
    }


def test_job_with_all_checks_for_asset():
    job_def = define_asset_job("job1", selection=Selection.checks_for_asset(asset1))
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 0
    check_evals = result.get_asset_check_evaluations()
    assert {check_eval.handle for check_eval in check_evals} == {
        AssetCheckHandle(asset1.key, "asset1_check1"),
        AssetCheckHandle(asset1.key, "asset1_check2"),
    }


def test_job_with_asset_and_all_its_checks():
    job_def = define_asset_job("job1", selection=Selection.assets(asset1))
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 1
    check_evals = result.get_asset_check_evaluations()
    assert {check_eval.handle for check_eval in check_evals} == {
        AssetCheckHandle(asset1.key, "asset1_check1"),
        AssetCheckHandle(asset1.key, "asset1_check2"),
    }


def test_job_with_single_check():
    job_def = define_asset_job("job1", selection=Selection.asset_checks(asset1_check1))
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 0
    check_evals = result.get_asset_check_evaluations()
    assert {check_eval.handle for check_eval in check_evals} == {
        AssetCheckHandle(asset1.key, "asset1_check1"),
    }


def test_job_with_all_assets_but_no_checks():
    job_def = define_asset_job(
        "job1", selection=Selection.all_assets() - Selection.all_asset_checks(asset1_check1)
    )
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 2
    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 0


def test_job_with_asset_without_its_checks():
    job_def = define_asset_job(
        "job1", selection=Selection.assets(asset1) - Selection.all_asset_checks()
    )
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 1
    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 0


def test_job_with_all_assets_and_all_checks():
    job_def = define_asset_job("job1", selection=Selection.all_assets())
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 2
    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 3


def test_job_with_all_assets_and_all_but_one_check():
    job_def = define_asset_job(
        "job1", selection=Selection.all_assets() - Selection.asset_checks(asset1_check1)
    )
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 2
    check_evals = result.get_asset_check_evaluations()
    assert {check_eval.handle for check_eval in check_evals} == {
        AssetCheckHandle(asset1.key, "asset1_check2"),
        AssetCheckHandle(asset2.key, "asset2_check1"),
    }


def test_include_asset_after_excluding_checks():
    job_def = define_asset_job(
        "job1",
        selection=(Selection.all_assets() - Selection.all_asset_checks())
        & Selection.assets(asset1),
    )
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 2
    check_evals = result.get_asset_check_evaluations()
    assert {check_eval.handle for check_eval in check_evals} == {
        AssetCheckHandle(asset1.key, "asset1_check1"),
        AssetCheckHandle(asset1.key, "asset1_check2"),
    }
