import pytest
from dagster import (
    AssetCheckKey,
    AssetCheckResult,
    AssetCheckSpec,
    AssetKey,
    AssetMaterialization,
    AssetSpec,
    AutomationCondition,
    DagsterInstance,
    Definitions,
    MaterializeResult,
    asset,
    asset_check,
    evaluate_automation_conditions,
)
from dagster._core.definitions import materialize
from dagster._core.definitions.declarative_automation.automation_condition import AutomationResult
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext

from dagster_tests.declarative_automation_tests.scenario_utils.automation_condition_scenario import (
    AutomationConditionScenarioState,
)
from dagster_tests.declarative_automation_tests.scenario_utils.scenario_specs import (
    two_partitions_def,
)
from dagster_tests.declarative_automation_tests.scenario_utils.scenario_state import ScenarioSpec

one_asset_two_checks = ScenarioSpec(
    asset_specs=[AssetSpec("A")],
    check_specs=[
        AssetCheckSpec("a1", asset="A", blocking=True),
        AssetCheckSpec("a2", asset="A"),
    ],
)
downstream_of_check = ScenarioSpec(
    asset_specs=[
        AssetSpec("A"),
        AssetSpec("B"),
        AssetSpec("C", deps=["A"]),
        AssetSpec("D", deps=["B"]),
    ],
    check_specs=[AssetCheckSpec("check", asset="A")],
)


def get_hardcoded_condition():
    true_set = set()

    class HardcodedCondition(AutomationCondition):
        @property
        def description(self) -> str:
            return "..."

        def evaluate(self, context: AutomationContext) -> AutomationResult:
            true_subset = (
                context.asset_graph_view.get_full_subset(key=context.key)
                if context.key in true_set
                else context.asset_graph_view.get_empty_subset(key=context.key)
            )
            return AutomationResult(context, true_subset=true_subset)

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

    true_set.add(AssetCheckKey(AssetKey("A"), "a1"))
    state, result = await state.evaluate("A")
    if is_any:
        assert result.true_subset.size == 2
    else:
        assert result.true_subset.size == (2 if blocking_only else 0)

    true_set.add(AssetCheckKey(AssetKey("A"), "a2"))
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


def test_all_deps_blocking_checks_passed_condition() -> None:
    @asset
    def A() -> None: ...

    @asset(deps=[A], automation_condition=AutomationCondition.all_deps_blocking_checks_passed())
    def B() -> None: ...

    @asset_check(asset=A, blocking=True)
    def blocking1(context) -> AssetCheckResult:
        passed = "passed" in context.run.tags
        return AssetCheckResult(passed=passed)

    @asset_check(asset=A, blocking=True)
    def blocking2(context) -> AssetCheckResult:
        passed = "passed" in context.run.tags
        return AssetCheckResult(passed=passed)

    @asset_check(asset=A, blocking=False)
    def nonblocking1(context) -> AssetCheckResult:
        passed = "passed" in context.run.tags
        return AssetCheckResult(passed=passed)

    @asset_check(asset=B, blocking=True)
    def blocking3(context) -> AssetCheckResult:
        passed = "passed" in context.run.tags
        return AssetCheckResult(passed=passed)

    defs = Definitions(assets=[A, B], asset_checks=[blocking1, blocking2, blocking3, nonblocking1])
    instance = DagsterInstance.ephemeral()

    # no checks evaluated
    result = evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.total_requested == 0

    # blocking1 passes, still not all of them
    defs.get_implicit_global_asset_job_def().get_subset(
        asset_check_selection={blocking1.check_key}
    ).execute_in_process(tags={"passed": ""}, instance=instance)
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # blocking2 passes, now all have passed
    defs.get_implicit_global_asset_job_def().get_subset(
        asset_check_selection={blocking2.check_key}
    ).execute_in_process(tags={"passed": ""}, instance=instance)
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # blocking3 fails, no impact (as it's not on a dep)
    defs.get_implicit_global_asset_job_def().get_subset(
        asset_check_selection={blocking3.check_key}
    ).execute_in_process(instance=instance, raise_on_error=False)
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # nonblocking1 fails, no impact (as it's non-blocking)
    defs.get_implicit_global_asset_job_def().get_subset(
        asset_check_selection={nonblocking1.check_key}
    ).execute_in_process(instance=instance, raise_on_error=False)
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # now A gets rematerialized, blocking checks haven't been executed yet
    instance.report_runless_asset_event(AssetMaterialization("A"))
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # blocking1 passes, but blocking2 fails
    defs.get_implicit_global_asset_job_def().get_subset(
        asset_check_selection={blocking1.check_key}
    ).execute_in_process(tags={"passed": ""}, instance=instance)
    defs.get_implicit_global_asset_job_def().get_subset(
        asset_check_selection={blocking2.check_key}
    ).execute_in_process(instance=instance, raise_on_error=False)
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # now blocking2 passes
    defs.get_implicit_global_asset_job_def().get_subset(
        asset_check_selection={blocking2.check_key}
    ).execute_in_process(tags={"passed": ""}, instance=instance)
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1


def test_blocking_checks_with_eager() -> None:
    cond = AutomationCondition.eager() & AutomationCondition.all_deps_blocking_checks_passed()

    @asset
    def root() -> None: ...

    @asset(
        deps=[root],
        automation_condition=cond,
        check_specs=[AssetCheckSpec("x", asset="A", blocking=True)],
    )
    def A() -> MaterializeResult:
        return MaterializeResult(check_results=[AssetCheckResult(passed=True)])

    @asset(deps=[A], automation_condition=cond)
    def B() -> None: ...

    defs = Definitions(assets=[root, A, B])
    instance = DagsterInstance.ephemeral()

    # nothing to do yet
    result = evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.total_requested == 0

    # root is materialized, should kick off a run of both A and B
    instance.report_runless_asset_event(AssetMaterialization("root"))
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 2

    # don't launch again
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # A is materialized in a vacuum (technically impossible), don't kick off
    instance.report_runless_asset_event(AssetMaterialization("A"))
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # A is now materialized with its check, do kick off B
    materialize([A], instance=instance)
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # don't launch again
    result = evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0
