from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.declarative_automation.operators import NewlyTrueCondition
from dagster._core.definitions.events import AssetKeyPartitionKey

from ...scenario_utils.automation_condition_scenario import AutomationConditionScenarioState
from ...scenario_utils.scenario_specs import one_asset
from .test_dep_condition import get_hardcoded_condition


def test_newly_true_condition() -> None:
    inner_condition, true_set = get_hardcoded_condition()

    condition = NewlyTrueCondition(operand=inner_condition)
    state = AutomationConditionScenarioState(one_asset, automation_condition=condition)

    # nothing true
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # becomes true
    true_set.add(AssetKeyPartitionKey(AssetKey("A")))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    # now on the next tick, this asset is no longer newly true
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # see above
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # see above
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # now condition becomes false, result still false
    true_set.remove(AssetKeyPartitionKey(AssetKey("A")))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # see above
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # becomes true again
    true_set.add(AssetKeyPartitionKey(AssetKey("A")))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    # no longer newly true
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0
