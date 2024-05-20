from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.declarative_scheduling import TriggerSinceTargetCondition
from dagster._core.definitions.events import AssetKeyPartitionKey

from ..scenario_specs import one_asset
from .asset_condition_scenario import SchedulingConditionScenarioState
from .test_dep_condition import get_hardcoded_condition


def test_trigger_since_y_unpartitioned() -> None:
    trigger_condition, true_set_trigger = get_hardcoded_condition()
    target_condition, true_set_target = get_hardcoded_condition()

    condition = TriggerSinceTargetCondition(
        trigger_condition=trigger_condition, target_condition=target_condition
    )
    state = SchedulingConditionScenarioState(one_asset, scheduling_condition=condition)

    # nothing true
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # trigger becomes true, but target has never been true
    true_set_trigger.add(AssetKeyPartitionKey(AssetKey("A")))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0
    true_set_trigger.remove(AssetKeyPartitionKey(AssetKey("A")))

    # target becomes true, but it's after trigger
    true_set_target.add(AssetKeyPartitionKey(AssetKey("A")))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0
    true_set_target.remove(AssetKeyPartitionKey(AssetKey("A")))

    # trigger becomes true again, and it's since target has become true
    true_set_trigger.add(AssetKeyPartitionKey(AssetKey("A")))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1
    true_set_trigger.remove(AssetKeyPartitionKey(AssetKey("A")))

    # remains true on the netriggert evaluation
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    # trigger becomes true again, still doesn't change anything
    true_set_trigger.add(AssetKeyPartitionKey(AssetKey("A")))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1
    true_set_trigger.remove(AssetKeyPartitionKey(AssetKey("A")))

    # now target becomes true again
    true_set_target.add(AssetKeyPartitionKey(AssetKey("A")))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0
    true_set_target.remove(AssetKeyPartitionKey(AssetKey("A")))

    # remains false on the netriggert evaluation
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0
