from dagster import (
    AssetCheckHandle,
    AssetCheckResult,
    AssetCheckSelection,
    AssetSelection,
    Definitions,
    ExecuteInProcessResult,
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
    job_def = define_asset_job("job1", selection=AssetCheckSelection.all())
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
    job_def = define_asset_job("job1", selection=AssetCheckSelection.checks_for_asset(asset1))
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 0
    check_evals = result.get_asset_check_evaluations()
    assert {check_eval.handle for check_eval in check_evals} == {
        AssetCheckHandle(asset1.key, "asset1_check1"),
        AssetCheckHandle(asset1.key, "asset1_check2"),
    }


def test_job_with_asset_and_all_its_checks():
    job_def = define_asset_job("job1", selection=AssetSelection.assets(asset1).with_checks())
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 1
    check_evals = result.get_asset_check_evaluations()
    assert {check_eval.handle for check_eval in check_evals} == {
        AssetCheckHandle(asset1.key, "asset1_check1"),
        AssetCheckHandle(asset1.key, "asset1_check2"),
    }


def test_job_with_single_check():
    job_def = define_asset_job("job1", selection=AssetCheckSelection.asset_checks(asset1_check1))
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 0
    check_evals = result.get_asset_check_evaluations()
    assert {check_eval.handle for check_eval in check_evals} == {
        AssetCheckHandle(asset1.key, "asset1_check1"),
    }


def test_job_with_all_assets_but_no_checks():
    job_def = define_asset_job("job1", selection=AssetSelection.all())
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 2
    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 0


def test_job_with_asset_without_its_checks():
    job_def = define_asset_job("job1", selection=AssetSelection.assets(asset1))
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 1
    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 0


def test_job_with_all_assets_and_all_their_checks():
    job_def = define_asset_job("job1", selection=AssetSelection.all().with_checks())
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 2
    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 3


def test_job_with_all_assets_and_all_but_one_check():
    job_def = define_asset_job(
        "job1",
        selection=AssetSelection.all_assets().with_checks()
        - AssetCheckSelection.asset_checks(asset1_check1),
    )
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 2
    check_evals = result.get_asset_check_evaluations()
    assert {check_eval.handle for check_eval in check_evals} == {
        AssetCheckHandle(asset1.key, "asset1_check2"),
        AssetCheckHandle(asset2.key, "asset2_check1"),
    }
