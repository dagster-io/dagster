import datetime

from dagster import SchedulingCondition

from ..scenario_specs import one_asset, two_partitions_def
from .asset_condition_scenario import SchedulingConditionScenarioState


def test_scheduled_since_unpartitioned() -> None:
    state = SchedulingConditionScenarioState(
        one_asset,
        scheduling_condition=~SchedulingCondition.scheduled_since(
            lookback_delta=datetime.timedelta(hours=1)
        ),
        # this condition depends on having non-empty results
        ensure_empty_result=False,
    )

    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    # the last tick would have requested the asset for materialization
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # now it's been more than an hour since the last request
    state = state.with_current_time_advanced(hours=1, seconds=1)
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    # edge case: one hour passes in between a request and the next evaluation
    state = state.with_current_time_advanced(hours=1)
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0


def test_scheduled_since_partitioned() -> None:
    state = SchedulingConditionScenarioState(
        one_asset,
        scheduling_condition=~SchedulingCondition.scheduled_since(
            lookback_delta=datetime.timedelta(hours=1)
        ),
        # this condition depends on having non-empty results
        ensure_empty_result=False,
    ).with_asset_properties(partitions_def=two_partitions_def)

    state, result = state.evaluate("A")
    assert result.true_subset.size == 2

    # the last tick would have requested both assets for materialization
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # now it's been more than an hour since the last request
    state = state.with_current_time_advanced(hours=1, seconds=1)
    state, result = state.evaluate("A")
    assert result.true_subset.size == 2

    # edge case: one hour passes in between a request and the next evaluation
    state = state.with_current_time_advanced(hours=1)
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0
