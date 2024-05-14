from dagster import SchedulingCondition

from dagster_tests.definitions_tests.auto_materialize_tests.base_scenario import run_request

from ..scenario_specs import one_asset, two_partitions_def
from .asset_condition_scenario import AssetConditionScenarioState


def test_updated_since_cron_unpartitioned() -> None:
    state = AssetConditionScenarioState(
        one_asset, asset_condition=SchedulingCondition.updated_since_cron(cron_schedule="0 * * * *")
    ).with_current_time("2020-02-02T01:05:00")

    state, result = state.evaluate("A")
    assert result.true_subset.size == 0

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
        AssetConditionScenarioState(
            one_asset,
            asset_condition=SchedulingCondition.updated_since_cron(cron_schedule="0 * * * *"),
        )
        .with_asset_properties(partitions_def=two_partitions_def)
        .with_current_time("2020-02-02T01:05:00")
    )

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

    # A 1 materialized again before the hour, A 2 materialized after the hour
    state = state.with_runs(run_request("A", "1"))
    state = state.with_current_time_advanced(hours=1)
    state = state.with_runs(run_request("A", "2"))
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1
