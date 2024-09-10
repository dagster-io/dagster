import pytest
from dagster import (
    AssetCheckKey,
    AssetCheckResult,
    AssetCheckSpec,
    AssetExecutionContext,
    AssetKey,
    AutomationCondition,
    Definitions,
    asset,
    asset_check,
    evaluate_automation_conditions,
    instance_for_test,
)
from dagster._core.definitions.result import MaterializeResult
from dagster._core.storage.asset_check_execution_record import (
    AssetCheckExecutionResolvedStatus as ACS,
)


def _get_defs(status: ACS, automation_condition: AutomationCondition) -> Definitions:
    @asset
    def a() -> None: ...

    @asset_check(asset=a, automation_condition=automation_condition)
    def some_check() -> AssetCheckResult:
        if status == ACS.SUCCEEDED:
            return AssetCheckResult(passed=True)
        elif status == ACS.FAILED:
            return AssetCheckResult(passed=False)
        elif status == ACS.EXECUTION_FAILED:
            raise Exception("fail")
        else:
            raise Exception(f"unexpected status {status}")

    return Definitions(assets=[a], asset_checks=[some_check])


@pytest.mark.parametrize(
    "status, automation_condition",
    [
        (ACS.SUCCEEDED, AutomationCondition.check.succeeded()),
        (ACS.FAILED, AutomationCondition.check.failed()),
    ],
)
def test_status_conditions_basic(status: ACS, automation_condition: AutomationCondition) -> None:
    defs = _get_defs(status, automation_condition)
    asset_job = defs.get_implicit_global_asset_job_def()
    a_job = asset_job.get_subset(asset_selection={AssetKey("a")}, asset_check_selection=set())
    some_check_job = asset_job.get_subset(
        asset_check_selection={AssetCheckKey(AssetKey("a"), "some_check")}
    )

    with instance_for_test() as instance:
        # no status as there hasn't been a materialization yet
        assert evaluate_automation_conditions(defs, instance).total_requested == 0

        a_job.execute_in_process(instance=instance)

        # no status as the check hasn't executed yet
        assert evaluate_automation_conditions(defs, instance).total_requested == 0

        some_check_job.execute_in_process(instance=instance, raise_on_error=False)

        # now the check gets requested because it has a status matching the condition
        assert evaluate_automation_conditions(defs, instance).total_requested == 1

        a_job.execute_in_process(instance=instance)

        # now the check has been executed less recently than the asset, so it goes back to false
        assert evaluate_automation_conditions(defs, instance).total_requested == 0


def test_check_not_executed() -> None:
    @asset(
        automation_condition=~AutomationCondition.any_checks_match(
            AutomationCondition.check.not_executed(),
        )
    )
    def A() -> None: ...

    @asset_check(asset=A)
    def c0() -> AssetCheckResult:
        return AssetCheckResult(check_name="c0", passed=True)

    @asset_check(asset=A)
    def c1() -> AssetCheckResult:
        return AssetCheckResult(check_name="c1", passed=True)

    @asset_check(asset=A)
    def c2() -> AssetCheckResult:
        return AssetCheckResult(check_name="c2", passed=True)

    defs = Definitions(assets=[A], asset_checks=[c0, c1, c2])
    asset_job = defs.get_implicit_global_asset_job_def()

    with instance_for_test() as instance:
        # no checks executed
        assert evaluate_automation_conditions(defs, instance).total_requested == 0

        asset_job.get_subset(
            asset_check_selection={AssetCheckKey(AssetKey("A"), name="c0")}
        ).execute_in_process(instance=instance)

        asset_job.get_subset(
            asset_check_selection={AssetCheckKey(AssetKey("A"), name="c1")}
        ).execute_in_process(instance=instance)

        # still one check not executed
        assert evaluate_automation_conditions(defs, instance).total_requested == 0

        asset_job.get_subset(
            asset_check_selection={AssetCheckKey(AssetKey("A"), name="c2")}
        ).execute_in_process(instance=instance)

        # all checks executed
        assert evaluate_automation_conditions(defs, instance).total_requested == 1


def test_all_deps_blocking_checks_succeeded() -> None:
    @asset(
        check_specs=[
            AssetCheckSpec(name="b", asset="A", blocking=True),
            AssetCheckSpec(name="nb", asset="A", blocking=False),
        ]
    )
    def A(context: AssetExecutionContext):
        return MaterializeResult(
            check_results=[
                AssetCheckResult(check_name="b", passed="a_fail_b" not in context.run_tags),
                AssetCheckResult(check_name="nb", passed="a_fail_nb" not in context.run_tags),
            ]
        )

    @asset(
        check_specs=[
            AssetCheckSpec(name="b", asset="B", blocking=True),
            AssetCheckSpec(name="nb", asset="B", blocking=False),
        ]
    )
    def B(context: AssetExecutionContext):
        return MaterializeResult(
            check_results=[
                AssetCheckResult(check_name="b", passed="b_fail_b" not in context.run_tags),
                AssetCheckResult(check_name="nb", passed="b_fail_nb" not in context.run_tags),
            ]
        )

    @asset(
        deps=[A, B],
        automation_condition=AutomationCondition.eager()
        & AutomationCondition.all_deps_blocking_checks_succeeded(),
    )
    def C() -> None: ...

    defs = Definitions(assets=[A, B, C])
    a_b_job = defs.get_implicit_global_asset_job_def().get_subset(
        asset_selection={AssetKey("A"), AssetKey("B")}
    )

    with instance_for_test() as instance:
        # no checks have executed
        result = evaluate_automation_conditions(defs=defs, instance=instance)
        assert result.total_requested == 0

        a_b_job.execute_in_process(instance=instance)

        # now all checks have executed successfully
        result = evaluate_automation_conditions(defs=defs, instance=instance)
        assert result.total_requested == 1

        # now a non-blocking check fails, still ok to execute
        a_b_job.execute_in_process(instance=instance, tags={"a_fail_nb": "True"})
        result = evaluate_automation_conditions(defs=defs, instance=instance)
        assert result.total_requested == 1

        # now a blocking check fails, don't execute
        a_b_job.execute_in_process(
            instance=instance, tags={"b_fail_b": "True"}, raise_on_error=False
        )
        result = evaluate_automation_conditions(defs=defs, instance=instance)
        assert result.total_requested == 0
