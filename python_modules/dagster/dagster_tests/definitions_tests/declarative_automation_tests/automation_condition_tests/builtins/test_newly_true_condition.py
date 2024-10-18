from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.events import AssetKeyPartitionKey

from dagster_tests.definitions_tests.declarative_automation_tests.automation_condition_tests.builtins.test_dep_condition import (
    get_hardcoded_condition,
)
from dagster_tests.definitions_tests.declarative_automation_tests.scenario_utils.automation_condition_scenario import (
    AutomationConditionScenarioState,
)
from dagster_tests.definitions_tests.declarative_automation_tests.scenario_utils.scenario_specs import (
    one_asset,
)


def test_newly_true_condition() -> None:
    inner_condition, true_set = get_hardcoded_condition()

    condition = inner_condition.newly_true()
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
