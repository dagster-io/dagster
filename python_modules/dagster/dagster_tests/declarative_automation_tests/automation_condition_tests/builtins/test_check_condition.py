import time
from collections.abc import Set

import dagster as dg
import pytest
from dagster import AssetSelection, AutomationCondition, AutomationContext, DagsterInstance

from dagster_tests.declarative_automation_tests.scenario_utils.automation_condition_scenario import (
    AutomationConditionScenarioState,
)
from dagster_tests.declarative_automation_tests.scenario_utils.scenario_specs import (
    two_partitions_def,
)
from dagster_tests.declarative_automation_tests.scenario_utils.scenario_state import ScenarioSpec

one_asset_two_checks = ScenarioSpec(
    asset_specs=[dg.AssetSpec("A")],
    check_specs=[
        dg.AssetCheckSpec("a1", asset="A", blocking=True),
        dg.AssetCheckSpec("a2", asset="A"),
    ],
)
downstream_of_check = ScenarioSpec(
    asset_specs=[
        dg.AssetSpec("A"),
        dg.AssetSpec("B"),
        dg.AssetSpec("C", deps=["A"]),
        dg.AssetSpec("D", deps=["B"]),
    ],
    check_specs=[dg.AssetCheckSpec("check", asset="A")],
)


def get_hardcoded_condition():
    true_set = set()

    class HardcodedCondition(dg.AutomationCondition):
        @property
        def description(self) -> str:
            return "..."

        def evaluate(self, context: AutomationContext) -> dg.AutomationResult:
            true_subset = (
                context.asset_graph_view.get_full_subset(key=context.key)
                if context.key in true_set
                else context.asset_graph_view.get_empty_subset(key=context.key)
            )
            return dg.AutomationResult(context, true_subset=true_subset)

    return HardcodedCondition(), true_set


@pytest.mark.asyncio
@pytest.mark.parametrize("is_any", [True, False])
@pytest.mark.parametrize("blocking_only", [True, False])
async def test_check_operators_partitioned(is_any: bool, blocking_only: bool) -> None:
    inner_condition, true_set = get_hardcoded_condition()
    condition = (
        AutomationCondition.any_checks_match(inner_condition, blocking_only=blocking_only)
        if is_any
        else AutomationCondition.all_checks_match(inner_condition, blocking_only=blocking_only)
    )
    state = AutomationConditionScenarioState(
        one_asset_two_checks, automation_condition=condition
    ).with_asset_properties(partitions_def=two_partitions_def)

    # no checks true
    state, result = await state.evaluate("A")
    assert result.true_subset.size == 0

    true_set.add(dg.AssetCheckKey(dg.AssetKey("A"), "a1"))
    state, result = await state.evaluate("A")
    if is_any:
        assert result.true_subset.size == 2
    else:
        assert result.true_subset.size == (2 if blocking_only else 0)

    true_set.add(dg.AssetCheckKey(dg.AssetKey("A"), "a2"))
    state, result = await state.evaluate("A")
    if is_any:
        assert result.true_subset.size == 2
    else:
        assert result.true_subset.size == 2


@pytest.mark.asyncio
async def test_any_checks_match_basic() -> None:
    # always true
    true_condition = AutomationCondition.cron_tick_passed(
        "* * * * *"
    ) | ~AutomationCondition.cron_tick_passed("* * * * *")

    condition = AutomationCondition.any_deps_match(
        AutomationCondition.any_checks_match(true_condition)
    )

    state = AutomationConditionScenarioState(downstream_of_check, automation_condition=condition)

    # there is an upstream check for C
    state, result = await state.evaluate("C")
    assert result.true_subset.size == 1

    # there is no upstream check for D
    state, result = await state.evaluate("D")
    assert result.true_subset.size == 0


@pytest.mark.parametrize("real_check", [True, False])
def test_all_deps_blocking_checks_passed_condition(real_check: bool) -> None:
    @dg.asset
    def A() -> None: ...

    @dg.asset(deps=[A], automation_condition=AutomationCondition.all_deps_blocking_checks_passed())
    def B() -> None: ...

    @dg.asset_check(asset=A, blocking=True)
    def blocking1(context) -> dg.AssetCheckResult:
        passed = "passed" in context.run.tags
        return dg.AssetCheckResult(passed=passed)

    @dg.asset_check(asset=A, blocking=True)
    def blocking2(context) -> dg.AssetCheckResult:
        passed = "passed" in context.run.tags
        return dg.AssetCheckResult(passed=passed)

    @dg.asset_check(asset=A, blocking=False)
    def nonblocking1(context) -> dg.AssetCheckResult:
        passed = "passed" in context.run.tags
        return dg.AssetCheckResult(passed=passed)

    @dg.asset_check(asset=B, blocking=True)
    def blocking3(context) -> dg.AssetCheckResult:
        passed = "passed" in context.run.tags
        return dg.AssetCheckResult(passed=passed)

    def _emit_check(checks: Set[dg.AssetCheckKey], passed: bool):
        if real_check:
            defs.resolve_implicit_global_asset_job_def().get_subset(
                asset_check_selection=checks
            ).execute_in_process(
                tags={"passed": ""} if passed else None, instance=instance, raise_on_error=passed
            )
        else:

            @dg.op
            def emit():
                for check in checks:
                    yield dg.AssetCheckEvaluation(
                        asset_key=check.asset_key, check_name=check.name, passed=passed
                    )
                yield dg.Output(None)

            @dg.job
            def emit_job():
                emit()

            emit_job.execute_in_process(instance=instance)

    defs = dg.Definitions(
        assets=[A, B], asset_checks=[blocking1, blocking2, blocking3, nonblocking1]
    )
    instance = DagsterInstance.ephemeral()

    # no checks evaluated
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.total_requested == 0

    # blocking1 passes, still not all of them
    _emit_check({blocking1.check_key}, True)
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # blocking2 passes, now all have passed
    _emit_check({blocking2.check_key}, True)
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # blocking3 fails, no impact (as it's not on a dep)
    _emit_check({blocking3.check_key}, False)
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # nonblocking1 fails, no impact (as it's non-blocking)
    _emit_check({nonblocking1.check_key}, False)
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # now A gets rematerialized, blocking checks haven't been executed yet
    instance.report_runless_asset_event(dg.AssetMaterialization("A"))

    # in sqlite the check evaluation create_timestamp is only second-level precision
    time.sleep(1)
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # blocking1 passes, but blocking2 fails
    _emit_check({blocking1.check_key}, True)
    _emit_check({blocking2.check_key}, False)
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # now blocking2 passes

    _emit_check({blocking2.check_key}, True)
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1


def test_blocking_checks_with_eager() -> None:
    cond = AutomationCondition.eager() & AutomationCondition.all_deps_blocking_checks_passed()

    @dg.asset
    def root() -> None: ...

    @dg.asset(
        deps=[root],
        automation_condition=cond,
        check_specs=[dg.AssetCheckSpec("x", asset="A", blocking=True)],
    )
    def A() -> dg.MaterializeResult:
        return dg.MaterializeResult(check_results=[dg.AssetCheckResult(passed=True)])

    @dg.asset(deps=[A], automation_condition=cond)
    def B() -> None: ...

    defs = dg.Definitions(assets=[root, A, B])
    instance = DagsterInstance.ephemeral()

    # nothing to do yet
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.total_requested == 0

    # root is materialized, should kick off a run of both A and B
    instance.report_runless_asset_event(dg.AssetMaterialization("root"))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 2

    # don't launch again
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # A is materialized in a vacuum (technically impossible), don't kick off
    instance.report_runless_asset_event(dg.AssetMaterialization("A"))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # A is now materialized with its check, do kick off B
    dg.materialize([A], instance=instance)
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # don't launch again
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0


@pytest.mark.parametrize(
    "condition",
    [
        AutomationCondition.any_deps_match(
            AutomationCondition.any_checks_match(AutomationCondition.check_failed()).allow(
                AssetSelection.checks(dg.AssetCheckKey(dg.AssetKey("A"), "allow_check"))
            ),
        ),
        AutomationCondition.any_deps_match(
            AutomationCondition.any_checks_match(AutomationCondition.check_failed()).ignore(
                AssetSelection.checks(dg.AssetCheckKey(dg.AssetKey("A"), "ignore_check"))
            ),
        ),
    ],
)
def test_check_selection(condition: AutomationCondition) -> None:
    @dg.asset
    def A() -> None: ...

    @dg.asset_check(asset=A)
    def ignore_check(context) -> dg.AssetCheckResult:
        passed = "passed" in context.run.tags
        return dg.AssetCheckResult(passed=passed)

    @dg.asset_check(asset=A)
    def allow_check(context) -> dg.AssetCheckResult:
        passed = "passed" in context.run.tags
        return dg.AssetCheckResult(passed=passed)

    @dg.asset(deps=[A], automation_condition=condition)
    def B() -> None: ...

    defs = dg.Definitions(assets=[A, B], asset_checks=[ignore_check, allow_check])
    instance = DagsterInstance.ephemeral()

    # no checks evaluated
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.total_requested == 0

    # ignore_check fails, but it's ignored
    defs.resolve_implicit_global_asset_job_def().get_subset(
        asset_check_selection={ignore_check.check_key}
    ).execute_in_process(instance=instance)
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # allow_check fails, not ignored
    defs.resolve_implicit_global_asset_job_def().get_subset(
        asset_check_selection={allow_check.check_key}
    ).execute_in_process(instance=instance, raise_on_error=False)
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # allow_check passes, now back to normal
    defs.resolve_implicit_global_asset_job_def().get_subset(
        asset_check_selection={allow_check.check_key}
    ).execute_in_process(tags={"passed": ""}, instance=instance)
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0


def test_any_check_invalid_selection() -> None:
    @dg.asset(
        automation_condition=dg.AutomationCondition.any_checks_match(
            AutomationCondition.missing()
        ).allow(
            dg.AssetSelection.checks(
                dg.AssetCheckKey(asset_key=dg.AssetKey("does_not_exist"), name="xyz")
            )
        )
    )
    def my_asset() -> None: ...

    instance = dg.DagsterInstance.ephemeral()
    result = dg.evaluate_automation_conditions(defs=[my_asset], instance=instance)

    assert result.total_requested == 0
