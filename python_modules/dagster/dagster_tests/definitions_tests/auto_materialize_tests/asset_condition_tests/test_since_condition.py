from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.declarative_automation import SinceCondition
from dagster._core.definitions.events import AssetPartitionKey

from ..scenario_specs import one_asset
from .asset_condition_scenario import AutomationConditionScenarioState
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
    true_set_primary.add(AssetPartitionKey(AssetKey("A")))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1
    true_set_primary.remove(AssetPartitionKey(AssetKey("A")))

    # reference becomes true, and it's after primary
    true_set_reference.add(AssetPartitionKey(AssetKey("A")))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0
    true_set_reference.remove(AssetPartitionKey(AssetKey("A")))

    # primary becomes true again, and it's since reference has become true
    true_set_primary.add(AssetPartitionKey(AssetKey("A")))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1
    true_set_primary.remove(AssetPartitionKey(AssetKey("A")))

    # remains true on the neprimaryt evaluation
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    # primary becomes true again, still doesn't change anything
    true_set_primary.add(AssetPartitionKey(AssetKey("A")))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1
    true_set_primary.remove(AssetPartitionKey(AssetKey("A")))

    # now reference becomes true again
    true_set_reference.add(AssetPartitionKey(AssetKey("A")))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0
    true_set_reference.remove(AssetPartitionKey(AssetKey("A")))

    # remains false on the neprimaryt evaluation
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0
