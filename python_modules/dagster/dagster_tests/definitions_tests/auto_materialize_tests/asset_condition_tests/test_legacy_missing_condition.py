import datetime

from dagster import AutoMaterializePolicy, Definitions, asset
from dagster._core.definitions.declarative_scheduling.legacy.asset_condition import (
    AssetCondition,
)
from dagster._core.definitions.declarative_scheduling.serialized_objects import (
    AssetConditionEvaluation,
)
from dagster._core.remote_representation.external_data import external_repository_data_from_def
from dagster._serdes import serialize_value
from dagster._serdes.serdes import deserialize_value

from ..base_scenario import run_request
from ..scenario_specs import (
    daily_partitions_def,
    day_partition_key,
    one_asset,
    time_partitions_start_datetime,
)
from .asset_condition_scenario import SchedulingConditionScenarioState


def test_missing_unpartitioned() -> None:
    state = SchedulingConditionScenarioState(
        one_asset, scheduling_condition=AssetCondition.missing()
    )

    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    evaluation1 = deserialize_value(
        serialize_value(AssetConditionEvaluation.from_result(result)), AssetConditionEvaluation
    )

    # still true
    state, result = state.evaluate("A")
    assert result.true_subset.size == 1

    evaluation2 = AssetConditionEvaluation.from_result(result)

    assert evaluation2.equivalent_to_stored_evaluation(evaluation1)

    # after a run of A it's now False
    state, result = state.with_runs(run_request("A")).evaluate("A")
    assert result.true_subset.size == 0

    # if we evaluate from scratch, it's also False
    _, result = state.without_cursor().evaluate("A")
    assert result.true_subset.size == 0


def test_missing_time_partitioned() -> None:
    state = (
        SchedulingConditionScenarioState(one_asset, scheduling_condition=AssetCondition.missing())
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
        run_request("A", day_partition_key(time_partitions_start_datetime, 2)),
        run_request("A", day_partition_key(time_partitions_start_datetime, 3)),
    ).evaluate("A")
    assert result.true_subset.size == 4

    # result is stable
    state, result = state.evaluate("A")
    assert result.true_subset.size == 4

    # if the partitions definition changes, then we have 1 fewer missing partition
    state = state.with_asset_properties(
        partitions_def=daily_partitions_def._replace(
            start=time_partitions_start_datetime + datetime.timedelta(days=1)
        )
    )
    state, result = state.evaluate("A")
    assert result.true_subset.size == 3

    # if we evaluate from scratch, get the same answer
    _, result = state.without_cursor().evaluate("A")
    assert result.true_subset.size == 3


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
