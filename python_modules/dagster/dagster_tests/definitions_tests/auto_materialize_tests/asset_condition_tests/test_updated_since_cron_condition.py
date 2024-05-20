from dagster import SchedulingCondition

from dagster_tests.definitions_tests.auto_materialize_tests.base_scenario import run_request

from ..scenario_specs import one_asset, two_partitions_def
from .asset_condition_scenario import SchedulingConditionScenarioState


def test_updated_since_cron_unpartitioned() -> None:
    state = SchedulingConditionScenarioState(
        one_asset,
        scheduling_condition=SchedulingCondition.newly_updated().since_last_cron_tick(
            cron_schedule="0 * * * *", cron_timezone="UTC"
        ),
    ).with_current_time("2020-02-02T00:55:00")

    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # now pass a cron tick, still haven't updated since that time
    state = state.with_current_time_advanced(minutes=10)
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # now A is updated, so have been updated since cron tick
    state = state.with_runs(run_request("A"))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    # new cron tick, no longer materialized since it
    state = state.with_current_time_advanced(hours=1)
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0


def test_updated_since_cron_partitioned() -> None:
    state = (
        SchedulingConditionScenarioState(
            one_asset,
            scheduling_condition=SchedulingCondition.newly_updated().since_last_cron_tick(
                cron_schedule="0 * * * *", cron_timezone="UTC"
            ),
        )
        .with_asset_properties(partitions_def=two_partitions_def)
        .with_current_time("2020-02-02T00:55:00")
    )

    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # now pass a cron tick, still haven't updated since that time
    state = state.with_current_time_advanced(minutes=10)
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # one materialized
    state = state.with_runs(run_request("A", "1"))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    # now both materialized
    state = state.with_runs(run_request("A", "2"))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 2

    # nothing changed
    state, result = state.evaluate("A")
    assert result.true_subset.size == 2

    # A 1 materialized again before the hour
    state = state.with_runs(run_request("A", "1"))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 2

    # new hour passes, nothing materialized since then
    state = state.with_current_time_advanced(hours=1)
    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

    # A 2 materialized again after the hour
    state = state.with_runs(run_request("A", "2"))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    # nothing changed
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1
