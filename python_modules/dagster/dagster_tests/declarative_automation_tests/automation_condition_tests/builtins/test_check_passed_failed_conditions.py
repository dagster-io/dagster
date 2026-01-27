import dagster as dg
import pytest
from dagster import AutomationCondition, DagsterInstance


@pytest.mark.parametrize("passed", [True, False])
def test_check_result_conditions(passed: bool) -> None:
    condition = AutomationCondition.check_passed() if passed else AutomationCondition.check_failed()

    @dg.asset
    def A() -> None: ...

    @dg.asset_check(asset=A, automation_condition=condition)
    def foo_check() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=passed)

    defs = dg.Definitions(assets=[A], asset_checks=[foo_check])
    instance = DagsterInstance.ephemeral()
    check_job = defs.resolve_implicit_global_asset_job_def().get_subset(
        asset_check_selection={foo_check.check_key}
    )

    # hasn't been executed
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.total_requested == 0

    # now gets executed, so the status matches
    check_job.execute_in_process(instance=instance)
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # stays true
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # now the parent asset gets materialized, which means that the status goes to "missing"
    instance.report_runless_asset_event(dg.AssetMaterialization("A"))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # now gets executed again, so the status matches
    check_job.execute_in_process(instance=instance)
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1


@pytest.mark.parametrize("passed", [True, False])
def test_partitioned_check_result_conditions(passed: bool) -> None:
    """Test check_passed/check_failed conditions with partitioned asset checks."""
    condition = AutomationCondition.check_passed() if passed else AutomationCondition.check_failed()
    partitions_def = dg.StaticPartitionsDefinition(["a", "b"])

    @dg.asset(partitions_def=partitions_def)
    def A() -> None: ...

    @dg.asset_check(asset=A, automation_condition=condition, partitions_def=partitions_def)
    def foo_check() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=passed)

    defs = dg.Definitions(assets=[A], asset_checks=[foo_check])
    instance = DagsterInstance.ephemeral()
    check_job = defs.resolve_implicit_global_asset_job_def().get_subset(
        asset_check_selection={foo_check.check_key}
    )

    # hasn't been executed for any partition
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.total_requested == 0

    # execute check for partition "a" only - now partition "a" matches
    check_job.execute_in_process(instance=instance, partition_key="a")
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # stays true for partition "a"
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # materialize partition "a" - check becomes stale for that partition
    instance.report_runless_asset_event(dg.AssetMaterialization("A", partition="a"))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # execute check for partition "a" again - back to matching
    check_job.execute_in_process(instance=instance, partition_key="a")
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # execute check for partition "b" - now both partitions match
    check_job.execute_in_process(instance=instance, partition_key="b")
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 2

    # materialize partition "b" - only partition "a" still matches
    instance.report_runless_asset_event(dg.AssetMaterialization("A", partition="b"))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1
