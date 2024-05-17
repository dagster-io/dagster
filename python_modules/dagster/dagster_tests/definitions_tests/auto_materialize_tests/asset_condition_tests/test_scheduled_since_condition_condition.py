from dagster import SchedulingCondition
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.events import AssetKeyPartitionKey

from dagster_tests.definitions_tests.auto_materialize_tests.base_scenario import run_request

from ..scenario_specs import two_assets_in_sequence
from .asset_condition_scenario import SchedulingConditionScenarioState
from .test_dep_condition import get_hardcoded_condition


def test_scheduled_since_condition() -> None:
    inner_condition, true_set = get_hardcoded_condition()

    state = SchedulingConditionScenarioState(
        two_assets_in_sequence,
        scheduling_condition=~SchedulingCondition.scheduled_since(
            SchedulingCondition.parent_newer()
        )
        & inner_condition,
        ensure_empty_result=False,
    ).with_current_time("2020-02-02T01:05:00")

    # for now, do not filter out any requests
    b_asset_partition = AssetKeyPartitionKey(AssetKey("B"))
    true_set.add(b_asset_partition)

    # never been scheduled
    state, result = state.evaluate("B")
    assert result.child_results[0].true_subset.size == 1
    assert result.true_subset.size == 1

    # requested on the previous tick, so this is now false
    state, result = state.evaluate("B")
    assert result.child_results[0].true_subset.size == 0
    assert result.true_subset.size == 0

    # still false, as nothing changed
    state, result = state.evaluate("B")
    assert result.child_results[0].true_subset.size == 0
    assert result.true_subset.size == 0

    # parent becomes now becomes newer, so not scheduled since that
    # also ensure that it does not get requested this tick
    true_set.remove(b_asset_partition)
    state = state.with_runs(run_request("A"))
    state, result = state.evaluate("B")
    assert result.child_results[0].true_subset.size == 1
    assert result.true_subset.size == 0

    # still has not been requested
    state, result = state.evaluate("B")
    assert result.child_results[0].true_subset.size == 1
    assert result.true_subset.size == 0

    # still has not been requested, and now we let it get requested again
    true_set.add(b_asset_partition)
    state, result = state.evaluate("B")
    assert result.child_results[0].true_subset.size == 1
    assert result.true_subset.size == 1

    # was requested on the previous tick, so everything False again
    state, result = state.evaluate("B")
    assert result.child_results[0].true_subset.size == 0
    assert result.true_subset.size == 0

    # B is materialized so no parent is newer anymore
    state = state.with_runs(run_request("B"))
    state, result = state.evaluate("B")
    assert result.child_results[0].true_subset.size == 0
    assert result.true_subset.size == 0

    # nothing changed
    state, result = state.evaluate("B")
    assert result.child_results[0].true_subset.size == 0
    assert result.true_subset.size == 0

    # parent updated again, immediately get requested
    state = state.with_runs(run_request("A"))
    state, result = state.evaluate("B")
    assert result.child_results[0].true_subset.size == 1
    assert result.true_subset.size == 1

    # next tick, don't get requested again
    state, result = state.evaluate("B")
    assert result.child_results[0].true_subset.size == 0
    assert result.true_subset.size == 0
