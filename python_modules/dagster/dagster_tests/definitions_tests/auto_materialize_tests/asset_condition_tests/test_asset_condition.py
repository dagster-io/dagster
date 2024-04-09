from dagster import AutoMaterializePolicy, Definitions, asset
from dagster._core.definitions.asset_condition.asset_condition import AssetCondition
from dagster._core.remote_representation.external_data import external_repository_data_from_def
from dagster._serdes import serialize_value

from ..base_scenario import run_request
from ..scenario_specs import (
    daily_partitions_def,
    day_partition_key,
    one_asset,
    time_partitions_start_datetime,
)
from .asset_condition_scenario import AssetConditionScenarioState


def test_missing_unpartitioned() -> None:
    state = AssetConditionScenarioState(one_asset, asset_condition=AssetCondition.missing())

    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    # still true
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    # after a run of A it's now False
    state, result = state.with_runs(run_request("A")).evaluate("A")
    assert result.true_subset.size == 0

    # if we evaluate from scratch, it's also False
    _, result = state.without_previous_evaluation_state().evaluate("A")
    assert result.true_subset.size == 0


def test_missing_time_partitioned() -> None:
    state = (
        AssetConditionScenarioState(one_asset, asset_condition=AssetCondition.missing())
        .with_asset_properties(partitions_def=daily_partitions_def)
        .with_current_time(time_partitions_start_datetime)
        .with_current_time_advanced(days=6, minutes=1)
    )

    state, result = state.evaluate("A")
    assert result.true_subset.size == 6

    # still true
    state, result = state.evaluate("A")
    assert result.true_subset.size == 6

    # after two runs of A those partitions are now False
    state, result = state.with_runs(
        run_request("A", day_partition_key(time_partitions_start_datetime, 1)),
        run_request("A", day_partition_key(time_partitions_start_datetime, 3)),
    ).evaluate("A")
    assert result.true_subset.size == 4

    # if we evaluate from scratch, they're still False
    _, result = state.without_previous_evaluation_state().evaluate("A")
    assert result.true_subset.size == 4


def test_serialize_definitions_with_asset_condition():
    amp = AutoMaterializePolicy.from_asset_condition(
        AssetCondition.parent_newer() & ~AssetCondition.updated_since_cron("0 * * * *")
    )

    @asset(auto_materialize_policy=amp)
    def my_asset():
        return 0

    result = serialize_value(
        external_repository_data_from_def(Definitions(assets=[my_asset]).get_repository_def())
    )
    assert isinstance(result, str)
