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


@pytest.mark.parametrize(
    "passed, severity, treat_warn_as_passed, expected_requested",
    [
        (True, dg.AssetCheckSeverity.ERROR, False, 1),
        (True, dg.AssetCheckSeverity.ERROR, True, 1),
        (False, dg.AssetCheckSeverity.WARN, False, 0),
        (False, dg.AssetCheckSeverity.WARN, True, 1),
        (False, dg.AssetCheckSeverity.ERROR, False, 0),
        (False, dg.AssetCheckSeverity.ERROR, True, 0),
    ],
)
def test_check_passed_treat_warn_as_passed(
    passed: bool,
    severity: dg.AssetCheckSeverity,
    treat_warn_as_passed: bool,
    expected_requested: int,
) -> None:
    @dg.asset
    def A() -> None: ...

    @dg.asset_check(
        asset=A,
        automation_condition=AutomationCondition.check_passed(
            treat_warn_as_passed=treat_warn_as_passed
        ),
    )
    def foo_check() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=passed, severity=severity)

    defs = dg.Definitions(assets=[A], asset_checks=[foo_check])
    instance = DagsterInstance.ephemeral()
    check_job = defs.resolve_implicit_global_asset_job_def().get_subset(
        asset_check_selection={foo_check.check_key}
    )

    result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.total_requested == 0

    check_job.execute_in_process(instance=instance)
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == expected_requested

    # a new materialization makes the check result stale, so nothing matches
    instance.report_runless_asset_event(dg.AssetMaterialization("A"))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0


@pytest.mark.parametrize(
    "severity, treat_warn_as_passed, expected_requested",
    [
        # a WARN on an upstream blocking check holds the child by default
        (dg.AssetCheckSeverity.WARN, False, 0),
        (dg.AssetCheckSeverity.WARN, True, 1),
        # an ERROR always holds the child
        (dg.AssetCheckSeverity.ERROR, False, 0),
        (dg.AssetCheckSeverity.ERROR, True, 0),
    ],
)
def test_all_deps_blocking_checks_passed_treat_warn_as_passed(
    severity: dg.AssetCheckSeverity, treat_warn_as_passed: bool, expected_requested: int
) -> None:
    @dg.asset
    def parent() -> None: ...

    @dg.asset_check(asset=parent, blocking=True)
    def parent_check() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=False, severity=severity)

    @dg.asset(
        deps=[parent],
        automation_condition=AutomationCondition.all_deps_blocking_checks_passed(
            treat_warn_as_passed=treat_warn_as_passed
        ),
    )
    def child() -> None: ...

    defs = dg.Definitions(assets=[parent, child], asset_checks=[parent_check])
    instance = DagsterInstance.ephemeral()

    # materialize the parent and run its blocking check in the same run
    result = dg.materialize([parent, parent_check], instance=instance, raise_on_error=False)
    assert result.get_asset_check_evaluations()[0].severity == severity

    result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.get_num_requested(child.key) == expected_requested


def test_treat_warn_as_passed_not_applied_to_partitioned_checks() -> None:
    partitions_def = dg.StaticPartitionsDefinition(["a"])

    @dg.asset(partitions_def=partitions_def)
    def A() -> None: ...

    @dg.asset_check(
        asset=A,
        automation_condition=AutomationCondition.check_passed(treat_warn_as_passed=True),
        partitions_def=partitions_def,
    )
    def foo_check() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=False, severity=dg.AssetCheckSeverity.WARN)

    defs = dg.Definitions(assets=[A], asset_checks=[foo_check])
    instance = DagsterInstance.ephemeral()
    check_job = defs.resolve_implicit_global_asset_job_def().get_subset(
        asset_check_selection={foo_check.check_key}
    )
    check_job.execute_in_process(instance=instance, partition_key="a")

    result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.total_requested == 0


def test_check_result_condition_serdes() -> None:
    from dagster._core.definitions.declarative_automation.operands import CheckResultCondition
    from dagster_shared.serdes import deserialize_value, serialize_value

    condition = CheckResultCondition(passed=True, treat_warn_as_passed=True)
    assert deserialize_value(serialize_value(condition), CheckResultCondition) == condition
    assert condition.name == "check_passed_or_warned"

    # payloads serialized before the field existed still load with the default
    old_payload = '{"__class__": "CheckResultCondition", "passed": true}'
    loaded = deserialize_value(old_payload, CheckResultCondition)
    assert loaded == CheckResultCondition(passed=True)
    assert loaded.treat_warn_as_passed is False
