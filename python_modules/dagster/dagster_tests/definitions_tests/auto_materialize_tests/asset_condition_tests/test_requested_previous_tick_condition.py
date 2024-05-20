from dagster._core.definitions.declarative_scheduling import NewlyRequestedCondition
from dagster._core.definitions.declarative_scheduling.scheduling_condition import SchedulingResult
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey

from ..scenario_specs import one_asset
from .asset_condition_scenario import SchedulingConditionScenarioState
from .test_dep_condition import get_hardcoded_condition


def test_requested_previous_tick() -> None:
    false_condition, _ = get_hardcoded_condition()
    hardcoded_condition, true_set = get_hardcoded_condition()
    state = SchedulingConditionScenarioState(
        one_asset,
        # this scheme allows us to set a value for the outer condition regardless of the value of
        # the inner condition
        scheduling_condition=(NewlyRequestedCondition() & false_condition) | hardcoded_condition,
        ensure_empty_result=False,
    )

    def get_result(result: SchedulingResult) -> SchedulingResult:
        # grab the inner result of this nested condition
        return result.child_results[0].child_results[0]

    # was not requested on the previous tick, as there was no tick
    state, result = state.evaluate("A")
    assert get_result(result).true_subset.size == 0

    # still was not requested on the previous tick
    state, result = state.evaluate("A")
    assert get_result(result).true_subset.size == 0

    # now we ensure that the asset does get requested this tick
    true_set.add(AssetKeyPartitionKey(AssetKey("A")))
    state, result = state.evaluate("A")
    # requested this tick, not the previous tick
    assert get_result(result).true_subset.size == 0
    true_set.remove(AssetKeyPartitionKey(AssetKey("A")))

    # requested on the previous tick
    state, result = state.evaluate("A")
    assert get_result(result).true_subset.size == 1

    # requested two ticks ago
    state, result = state.evaluate("A")
    assert get_result(result).true_subset.size == 0
