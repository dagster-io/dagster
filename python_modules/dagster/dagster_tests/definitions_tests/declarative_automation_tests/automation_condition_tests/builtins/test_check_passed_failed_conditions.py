import pytest
from dagster import (
    AssetCheckResult,
    AssetMaterialization,
    AutomationCondition,
    DagsterInstance,
    Definitions,
    asset,
    asset_check,
    evaluate_automation_conditions,
)


@pytest.mark.parametrize("passed", [True, False])
def test_check_result_conditions(passed: bool) -> None:
    condition = AutomationCondition.check_passed() if passed else AutomationCondition.check_failed()

    @asset
    def A() -> None: ...

    @asset_check(asset=A, automation_condition=condition)
    def foo_check() -> AssetCheckResult:
        return AssetCheckResult(passed=passed)

    defs = Definitions(assets=[A], asset_checks=[foo_check])
    instance = DagsterInstance.ephemeral()
    check_job = defs.get_implicit_global_asset_job_def().get_subset(
        asset_check_selection={foo_check.check_key}
    )

    # hasn't been executed
    result = evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.total_requested == 0

    # now gets executed, so the status matches
    check_job.execute_in_process(instance=instance)
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # stays true
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # now the parent asset gets materialized, which means that the status goes to "missing"
    instance.report_runless_asset_event(AssetMaterialization("A"))
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # now gets executed again, so the status matches
    check_job.execute_in_process(instance=instance)
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1
