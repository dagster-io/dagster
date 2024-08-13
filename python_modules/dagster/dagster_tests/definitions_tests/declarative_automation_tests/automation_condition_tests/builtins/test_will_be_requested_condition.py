from dagster import AssetKey, AutomationCondition
from dagster._core.definitions.events import AssetKeyPartitionKey

from ...scenario_utils.automation_condition_scenario import AutomationConditionScenarioState
from ...scenario_utils.scenario_specs import two_assets_in_sequence, two_partitions_def


def test_will_be_requested_unpartitioned() -> None:
    condition = AutomationCondition.any_deps_match(AutomationCondition.will_be_requested())
    state = AutomationConditionScenarioState(two_assets_in_sequence, automation_condition=condition)

    # no requested parents
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # parent is requested
    state = state.with_requested_asset_partitions([AssetKeyPartitionKey(AssetKey("A"))])
    state, result = state.evaluate("B")
    assert result.true_subset.size == 1


def test_will_be_requested_static_partitioned() -> None:
    condition = AutomationCondition.any_deps_match(AutomationCondition.will_be_requested())
    state = AutomationConditionScenarioState(
        two_assets_in_sequence, automation_condition=condition
    ).with_asset_properties(partitions_def=two_partitions_def)

    # no requested parents
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # one requested parent
    state = state.with_requested_asset_partitions([AssetKeyPartitionKey(AssetKey("A"), "1")])
    state, result = state.evaluate("B")
    assert result.true_subset.size == 1
    assert result.true_subset.asset_partitions == {AssetKeyPartitionKey(AssetKey("B"), "1")}

    # two requested parents
    state = state.with_requested_asset_partitions(
        [AssetKeyPartitionKey(AssetKey("A"), "1"), AssetKeyPartitionKey(AssetKey("A"), "2")]
    )
    state, result = state.evaluate("B")
    assert result.true_subset.size == 2


def test_will_be_requested_different_partitions() -> None:
    condition = AutomationCondition.any_deps_match(AutomationCondition.will_be_requested())
    state = AutomationConditionScenarioState(
        two_assets_in_sequence, automation_condition=condition
    ).with_asset_properties("A", partitions_def=two_partitions_def)

    # no requested parents
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # one requested parent, but can't execute in same run
    state = state.with_requested_asset_partitions([AssetKeyPartitionKey(AssetKey("A"), "1")])
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # two requested parents, but can't execute in same run
    state = state.with_requested_asset_partitions(
        [AssetKeyPartitionKey(AssetKey("A"), "1"), AssetKeyPartitionKey(AssetKey("A"), "2")]
    )
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0
