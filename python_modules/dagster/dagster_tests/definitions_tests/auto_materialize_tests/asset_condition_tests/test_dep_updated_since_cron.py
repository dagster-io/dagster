from dagster._core.definitions.asset_condition.asset_condition import (
    AssetCondition,
)

from ..base_scenario import run_request
from ..scenario_specs import (
    daily_partitions_def,
    day_partition_key,
    time_partitions_start_datetime,
    two_assets_in_sequence,
)
from .asset_condition_scenario import AssetConditionScenarioState


def test_dep_updated_since_cron_unpartitioned_to_unpartitioned() -> None:
    state = AssetConditionScenarioState(
        two_assets_in_sequence, asset_condition=AssetCondition.dep_updated_since_cron("@daily")
    ).with_current_time("2024-01-01 00:01:00")

    # dep never materialized
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # now dep is materialized
    state, result = state.with_runs(run_request("A")).evaluate("B")
    assert result.true_subset.size == 1

    # now it's a new cron tick
    state, result = state.with_current_time_advanced(days=1).evaluate("B")
    assert result.true_subset.size == 0

    # if we evaluate from scratch, it's also False
    _, result = state.without_previous_evaluation_state().evaluate("A")
    assert result.true_subset.size == 0


def test_dep_updated_since_cron_time_partitioned_to_unpartitioend() -> None:
    state = (
        AssetConditionScenarioState(
            two_assets_in_sequence, asset_condition=AssetCondition.dep_updated_since_cron("@daily")
        )
        .with_asset_properties("A", partitions_def=daily_partitions_def)
        .with_current_time(time_partitions_start_datetime)
        .with_current_time_advanced(days=3, minutes=1)
    )

    # dep never materialized
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # old partition of A materialized, doesn't count
    state = state.with_runs(run_request("A", day_partition_key(time_partitions_start_datetime, 1)))
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # newest partition of A materialized, counts!
    state = state.with_runs(run_request("A", day_partition_key(time_partitions_start_datetime, 3)))
    state, result = state.evaluate("B")
    assert result.true_subset.size == 1

    # now a day later, not new enough
    state = state.with_current_time_advanced(days=1)
    state, result = state.evaluate("B")
    assert result.true_subset.size == 0

    # if we evaluate from scratch, it's also False
    _, result = state.without_previous_evaluation_state().evaluate("B")
    assert result.true_subset.size == 0
