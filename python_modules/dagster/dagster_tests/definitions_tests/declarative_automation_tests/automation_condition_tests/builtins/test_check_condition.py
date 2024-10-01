import pytest
from dagster import AutomationCondition
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.declarative_automation.automation_condition import AutomationResult
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext

from dagster_tests.definitions_tests.declarative_automation_tests.scenario_utils.automation_condition_scenario import (
    AutomationConditionScenarioState,
)
from dagster_tests.definitions_tests.declarative_automation_tests.scenario_utils.scenario_specs import (
    two_partitions_def,
)
from dagster_tests.definitions_tests.declarative_automation_tests.scenario_utils.scenario_state import (
    ScenarioSpec,
)

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


@pytest.mark.parametrize("is_any", [True, False])
@pytest.mark.parametrize("blocking_only", [True, False])
def test_check_operators_partitioned(is_any: bool, blocking_only: bool) -> None:
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
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    true_set.add(AssetCheckKey(AssetKey("A"), "a1"))
    state, result = state.evaluate("A")
    if is_any:
        assert result.true_subset.size == 2
    else:
        assert result.true_subset.size == (2 if blocking_only else 0)

    true_set.add(AssetCheckKey(AssetKey("A"), "a2"))
    state, result = state.evaluate("A")
    if is_any:
        assert result.true_subset.size == 2
    else:
        assert result.true_subset.size == 2


def test_any_checks_match_basic() -> None:
    # always true
    true_condition = AutomationCondition.cron_tick_passed(
        "* * * * *"
    ) | ~AutomationCondition.cron_tick_passed("* * * * *")

    condition = AutomationCondition.any_deps_match(
        AutomationCondition.any_checks_match(true_condition)
    )

    state = AutomationConditionScenarioState(downstream_of_check, automation_condition=condition)

    # there is an upstream check for C
    state, result = state.evaluate("C")
    assert result.true_subset.size == 1

    # there is no upstream check for D
    state, result = state.evaluate("D")
    assert result.true_subset.size == 0
