import dagster as dg
import pytest
from dagster import AssetSelection
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition


@dg.asset
def asset1(): ...


@dg.asset
def asset2(): ...


@dg.asset_check(asset=asset1)
def asset1_check1():
    return dg.AssetCheckResult(passed=True)


@dg.asset_check(asset=asset1)
def asset1_check2():
    return dg.AssetCheckResult(passed=True)


@dg.asset_check(asset=asset2)
def asset2_check1():
    return dg.AssetCheckResult(passed=True)


def execute_asset_job_in_process(
    asset_job: UnresolvedAssetJobDefinition,
) -> dg.ExecuteInProcessResult:
    assets = [asset1, asset2]
    asset_checks = [asset1_check1, asset1_check2, asset2_check1]
    defs = dg.Definitions(assets=assets, jobs=[asset_job], asset_checks=asset_checks)
    job_def = defs.resolve_job_def(asset_job.name)
    return job_def.execute_in_process()


def test_job_with_all_checks_no_materializations():
    job_def = dg.define_asset_job("job1", selection=AssetSelection.all_asset_checks())
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 0
    check_evals = result.get_asset_check_evaluations()
    assert {check_eval.asset_check_key for check_eval in check_evals} == {
        dg.AssetCheckKey(asset1.key, "asset1_check1"),
        dg.AssetCheckKey(asset1.key, "asset1_check2"),
        dg.AssetCheckKey(asset2.key, "asset2_check1"),
    }


def test_job_with_all_checks_for_asset():
    job_def = dg.define_asset_job("job1", selection=AssetSelection.checks_for_assets(asset1))
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 0
    check_evals = result.get_asset_check_evaluations()
    assert {check_eval.asset_check_key for check_eval in check_evals} == {
        dg.AssetCheckKey(asset1.key, "asset1_check1"),
        dg.AssetCheckKey(asset1.key, "asset1_check2"),
    }


def test_checks_for_assets_asset_key_coercibles():
    @dg.asset
    def asset1(): ...

    @dg.asset_check(asset=asset1)
    def asset1_check():
        return dg.AssetCheckResult(passed=True)

    @dg.asset
    def asset2(): ...

    @dg.asset_check(asset=asset2)
    def asset2_check():
        return dg.AssetCheckResult(passed=True)

    defs = dg.Definitions(assets=[asset1, asset2], asset_checks=[asset1_check, asset2_check])
    asset_graph = defs.resolve_asset_graph()

    assert AssetSelection.checks_for_assets(asset1).resolve_checks(asset_graph) == {
        dg.AssetCheckKey(asset1.key, "asset1_check")
    }
    assert AssetSelection.checks_for_assets(asset1.key).resolve_checks(asset_graph) == {
        dg.AssetCheckKey(asset1.key, "asset1_check")
    }
    assert AssetSelection.checks_for_assets("asset1").resolve_checks(asset_graph) == {
        dg.AssetCheckKey(asset1.key, "asset1_check")
    }


def test_job_with_asset_and_all_its_checks():
    job_def = dg.define_asset_job("job1", selection=AssetSelection.assets(asset1))
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 1
    check_evals = result.get_asset_check_evaluations()
    assert {check_eval.asset_check_key for check_eval in check_evals} == {
        dg.AssetCheckKey(asset1.key, "asset1_check1"),
        dg.AssetCheckKey(asset1.key, "asset1_check2"),
    }


def test_job_with_single_check():
    job_def = dg.define_asset_job("job1", selection=AssetSelection.checks(asset1_check1))
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 0
    check_evals = result.get_asset_check_evaluations()
    assert {check_eval.asset_check_key for check_eval in check_evals} == {
        dg.AssetCheckKey(asset1.key, "asset1_check1"),
    }


def test_job_with_all_assets_but_no_checks():
    job_def = dg.define_asset_job(
        "job1", selection=AssetSelection.all() - AssetSelection.all_asset_checks()
    )
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 2
    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 0


def test_job_with_asset_without_its_checks():
    job_def = dg.define_asset_job(
        "job1", selection=AssetSelection.assets(asset1) - AssetSelection.all_asset_checks()
    )
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 1
    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 0

    job_def = dg.define_asset_job("job1", selection=AssetSelection.assets(asset1).without_checks())
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 1
    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 0


def test_job_with_all_assets_and_all_checks():
    job_def = dg.define_asset_job("job1", selection=AssetSelection.all())
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 2
    check_evals = result.get_asset_check_evaluations()
    assert len(check_evals) == 3


def test_job_with_all_assets_and_all_but_one_check():
    job_def = dg.define_asset_job(
        "job1", selection=AssetSelection.all() - AssetSelection.checks(asset1_check1)
    )
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 2
    check_evals = result.get_asset_check_evaluations()
    assert {check_eval.asset_check_key for check_eval in check_evals} == {
        dg.AssetCheckKey(asset1.key, "asset1_check2"),
        dg.AssetCheckKey(asset2.key, "asset2_check1"),
    }


def test_include_asset_after_excluding_checks():
    job_def = dg.define_asset_job(
        "job1",
        selection=(AssetSelection.all() - AssetSelection.all_asset_checks())
        | AssetSelection.assets(asset1),
    )
    result = execute_asset_job_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 2
    check_evals = result.get_asset_check_evaluations()
    assert {check_eval.asset_check_key for check_eval in check_evals} == {
        dg.AssetCheckKey(asset1.key, "asset1_check1"),
        dg.AssetCheckKey(asset1.key, "asset1_check2"),
    }


@dg.asset(
    check_specs=[
        dg.AssetCheckSpec(asset="asset_with_checks", name="check1"),
        dg.AssetCheckSpec(asset="asset_with_checks", name="check2"),
    ]
)
def asset_with_checks():
    yield dg.Output(1)
    yield dg.AssetCheckResult(passed=True, check_name="check1")
    yield dg.AssetCheckResult(passed=True, check_name="check2")


def execute_asset_job_2_in_process(
    asset_job: UnresolvedAssetJobDefinition,
) -> dg.ExecuteInProcessResult:
    assets = [asset_with_checks]
    defs = dg.Definitions(assets=assets, jobs=[asset_job])
    job_def = defs.resolve_job_def(asset_job.name)
    return job_def.execute_in_process()


def test_checks_on_asset():
    job_def = dg.define_asset_job("job2", selection=AssetSelection.all())
    result = execute_asset_job_2_in_process(job_def)
    assert result.success

    assert len(result.get_asset_materialization_events()) == 1
    check_evals = result.get_asset_check_evaluations()
    assert {check_eval.asset_check_key for check_eval in check_evals} == {
        dg.AssetCheckKey(asset_with_checks.key, "check1"),
        dg.AssetCheckKey(asset_with_checks.key, "check2"),
    }


def test_check_keys_selection():
    assets = [asset1, asset2]
    asset_checks = [asset1_check1, asset1_check2, asset2_check1]
    defs = dg.Definitions(assets=assets, asset_checks=asset_checks)
    asset_graph = defs.resolve_asset_graph()
    keys = {
        dg.AssetCheckKey(asset_key=asset1.key, name="asset1_check1"),
        dg.AssetCheckKey(asset_key=asset1.key, name="asset1_check2"),
    }
    assert AssetSelection.checks(*keys).resolve_checks(asset_graph) == keys

    fake_key = dg.AssetCheckKey(asset_key=asset1.key, name="fake")
    assert AssetSelection.checks(fake_key).resolve_checks(asset_graph, allow_missing=True) == set()

    with pytest.raises(
        dg.DagsterInvalidSubsetError,
        match=r"AssetCheckKey\(s\) \['asset1:fake'\] were selected, but no definitions supply these keys..*",
    ):
        AssetSelection.checks(fake_key).resolve_checks(asset_graph)
