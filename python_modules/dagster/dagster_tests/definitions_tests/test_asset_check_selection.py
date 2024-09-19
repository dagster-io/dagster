import pytest
from dagster import (
    AssetCheckResult,
    AssetSelection,
    Definitions,
    ExecuteInProcessResult,
    Output,
    asset,
    asset_check,
    define_asset_job,
)
from dagster._core.definitions.asset_check_spec import AssetCheckKey, AssetCheckSpec
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition
from dagster._core.errors import DagsterInvalidSubsetError


@asset
def asset1(): ...


@asset
def asset2(): ...


@asset_check(asset=asset1)
def asset1_check1():
    return AssetCheckResult(passed=True)


@asset_check(asset=asset1)
def asset1_check2():
    return AssetCheckResult(passed=True)


@asset_check(asset=asset2)
def asset2_check1():
    return AssetCheckResult(passed=True)


def execute_asset_job_in_process(asset_job: UnresolvedAssetJobDefinition) -> ExecuteInProcessResult:
    assets = [asset1, asset2]
    asset_checks = [asset1_check1, asset1_check2, asset2_check1]
    defs = Definitions(assets=assets, jobs=[asset_job], asset_checks=asset_checks)
    job_def = defs.get_job_def(asset_job.name)
    return job_def.execute_in_process()


def test_job_with_all_checks_no_materializations():
    job_def = define_asset_job("job1", selection=AssetSelection.all_asset_checks())
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 0
    check_evals = result.get_asset_check_evaluations()
    assert {check_eval.asset_check_key for check_eval in check_evals} == {
        AssetCheckKey(asset1.key, "asset1_check1"),
        AssetCheckKey(asset1.key, "asset1_check2"),
        AssetCheckKey(asset2.key, "asset2_check1"),
    }


def test_job_with_all_checks_for_asset():
    job_def = define_asset_job("job1", selection=AssetSelection.checks_for_assets(asset1))
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 0
    check_evals = result.get_asset_check_evaluations()
    assert {check_eval.asset_check_key for check_eval in check_evals} == {
        AssetCheckKey(asset1.key, "asset1_check1"),
        AssetCheckKey(asset1.key, "asset1_check2"),
    }


def test_job_with_asset_and_all_its_checks():
    job_def = define_asset_job("job1", selection=AssetSelection.assets(asset1))
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 1
    check_evals = result.get_asset_check_evaluations()
    assert {check_eval.asset_check_key for check_eval in check_evals} == {
        AssetCheckKey(asset1.key, "asset1_check1"),
        AssetCheckKey(asset1.key, "asset1_check2"),
    }


def test_job_with_single_check():
    job_def = define_asset_job("job1", selection=AssetSelection.checks(asset1_check1))
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 0
    check_evals = result.get_asset_check_evaluations()
    assert {check_eval.asset_check_key for check_eval in check_evals} == {
        AssetCheckKey(asset1.key, "asset1_check1"),
    }


def test_job_with_all_assets_but_no_checks():
    job_def = define_asset_job(
        "job1", selection=AssetSelection.all() - AssetSelection.all_asset_checks()
    )
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 2
    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 0


def test_job_with_asset_without_its_checks():
    job_def = define_asset_job(
        "job1", selection=AssetSelection.assets(asset1) - AssetSelection.all_asset_checks()
    )
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 1
    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 0

    job_def = define_asset_job("job1", selection=AssetSelection.assets(asset1).without_checks())
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 1
    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 0


def test_job_with_all_assets_and_all_checks():
    job_def = define_asset_job("job1", selection=AssetSelection.all())
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 2
    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 3


def test_job_with_all_assets_and_all_but_one_check():
    job_def = define_asset_job(
        "job1", selection=AssetSelection.all() - AssetSelection.checks(asset1_check1)
    )
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 2
    check_evals = result.get_asset_check_evaluations()
    assert {check_eval.asset_check_key for check_eval in check_evals} == {
        AssetCheckKey(asset1.key, "asset1_check2"),
        AssetCheckKey(asset2.key, "asset2_check1"),
    }


def test_include_asset_after_excluding_checks():
    job_def = define_asset_job(
        "job1",
        selection=(AssetSelection.all() - AssetSelection.all_asset_checks())
        | AssetSelection.assets(asset1),
    )
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 2
    check_evals = result.get_asset_check_evaluations()
    assert {check_eval.asset_check_key for check_eval in check_evals} == {
        AssetCheckKey(asset1.key, "asset1_check1"),
        AssetCheckKey(asset1.key, "asset1_check2"),
    }


@asset(
    check_specs=[
        AssetCheckSpec(asset="asset_with_checks", name="check1"),
        AssetCheckSpec(asset="asset_with_checks", name="check2"),
    ]
)
def asset_with_checks():
    yield Output(1)
    yield AssetCheckResult(passed=True, check_name="check1")
    yield AssetCheckResult(passed=True, check_name="check2")


def execute_asset_job_2_in_process(
    asset_job: UnresolvedAssetJobDefinition,
) -> ExecuteInProcessResult:
    assets = [asset_with_checks]
    defs = Definitions(assets=assets, jobs=[asset_job])
    job_def = defs.get_job_def(asset_job.name)
    return job_def.execute_in_process()


def test_checks_on_asset():
    job_def = define_asset_job("job2", selection=AssetSelection.all())
    result = execute_asset_job_2_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 1
    check_evals = result.get_asset_check_evaluations()
    assert {check_eval.asset_check_key for check_eval in check_evals} == {
        AssetCheckKey(asset_with_checks.key, "check1"),
        AssetCheckKey(asset_with_checks.key, "check2"),
    }


def test_check_keys_selection():
    assets = [asset1, asset2]
    asset_checks = [asset1_check1, asset1_check2, asset2_check1]
    defs = Definitions(assets=assets, asset_checks=asset_checks)
    asset_graph = defs.get_asset_graph()
    keys = {
        AssetCheckKey(asset_key=asset1.key, name="asset1_check1"),
        AssetCheckKey(asset_key=asset1.key, name="asset1_check2"),
    }
    assert AssetSelection.checks(*keys).resolve_checks(asset_graph) == keys

    fake_key = AssetCheckKey(asset_key=asset1.key, name="fake")
    assert AssetSelection.checks(fake_key).resolve_checks(asset_graph, allow_missing=True) == set()

    with pytest.raises(
        DagsterInvalidSubsetError,
        match=r"AssetCheckKey\(s\) \['asset1:fake'\] were selected, but no definitions supply these keys..*",
    ):
        AssetSelection.checks(fake_key).resolve_checks(asset_graph)
