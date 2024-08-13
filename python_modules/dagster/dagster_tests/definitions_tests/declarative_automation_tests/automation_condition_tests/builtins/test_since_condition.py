from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.declarative_automation.operators import SinceCondition
from dagster._core.definitions.events import AssetKeyPartitionKey

from ...scenario_utils.automation_condition_scenario import AutomationConditionScenarioState
from ...scenario_utils.scenario_specs import one_asset
from .test_dep_condition import get_hardcoded_condition


def test_since_condition_unpartitioned() -> None:
    primary_condition, true_set_primary = get_hardcoded_condition()
    reference_condition, true_set_reference = get_hardcoded_condition()

    condition = SinceCondition(
        trigger_condition=primary_condition, reset_condition=reference_condition
    )
    state = AutomationConditionScenarioState(one_asset, automation_condition=condition)

    # nothing true
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # primary becomes true, but reference has never been true
    true_set_primary.add(AssetKeyPartitionKey(AssetKey("A")))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1
    true_set_primary.remove(AssetKeyPartitionKey(AssetKey("A")))

    # reference becomes true, and it's after primary
    true_set_reference.add(AssetKeyPartitionKey(AssetKey("A")))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0
    true_set_reference.remove(AssetKeyPartitionKey(AssetKey("A")))

    # primary becomes true again, and it's since reference has become true
    true_set_primary.add(AssetKeyPartitionKey(AssetKey("A")))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1
    true_set_primary.remove(AssetKeyPartitionKey(AssetKey("A")))

    # remains true on the neprimaryt evaluation
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    # primary becomes true again, still doesn't change anything
    true_set_primary.add(AssetKeyPartitionKey(AssetKey("A")))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1
    true_set_primary.remove(AssetKeyPartitionKey(AssetKey("A")))

    # now reference becomes true again
    true_set_reference.add(AssetKeyPartitionKey(AssetKey("A")))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0
    true_set_reference.remove(AssetKeyPartitionKey(AssetKey("A")))

    # remains false on the neprimaryt evaluation
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0
